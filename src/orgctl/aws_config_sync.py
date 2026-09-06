"""Write `credential_process` profile blocks into ~/.aws/config for every
account (and optionally every role) in the local orgs.yaml registry.

Uses configparser so any profiles you already have — hand-written, from
`aws configure`, whatever — are preserved untouched. Every section this
tool writes carries a per-section marker key (`_orgctl_managed`, stripped
back out before display/use). On a re-run, a section is only ever
overwritten if that marker is already present; if a profile name collides
with a section that exists but wasn't created by this tool, it's left
alone and reported back as a conflict instead of being silently mutated.
"""

from __future__ import annotations

import configparser
import shutil
from pathlib import Path

from .config import Account, OrgConfig

# Written into every section this tool creates so a later run can tell
# "I made this, safe to overwrite" apart from "this collides with a
# profile the user already had". Stripped out again before the settings
# are ever compared/displayed/used as real profile config.
_MANAGED_KEY = "_orgctl_managed"


def aws_config_path() -> Path:
    return Path.home() / ".aws" / "config"


def _profile_name(prefix: str, account: Account, role: str, *, all_roles: bool) -> str:
    base = prefix or account.alias
    return f"{base}-{role}" if all_roles else base


def _managed_profiles_for(
    cfg: OrgConfig, prefix: str, all_roles: bool
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Build the set of profile-name -> settings this tool would write.

    Returns (profiles, skipped_aliases) — an account is skipped only in
    single-role mode when it has multiple roles and no configured
    `default_role`, since there'd be no unambiguous choice.
    """
    profiles: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    for account in cfg.accounts.values():
        if all_roles and account.roles:
            roles: list[str] = account.roles
        else:
            single = account.default_role or (account.roles[0] if len(account.roles) == 1 else None)
            if not single:
                skipped.append(account.alias)
                continue
            roles = [single]

        for role in roles:
            name = _profile_name(prefix, account, role, all_roles=all_roles)
            profiles[name] = {
                "credential_process": (
                    f"orgctl creds-process --account {account.alias} --role {role}"
                ),
                "region": cfg.default_region,
            }
    return profiles, skipped


def sync(
    cfg: OrgConfig,
    *,
    prefix: str = "",
    all_roles: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str], list[str], Path]:
    """Write/update profiles in ~/.aws/config for every account/role.

    Returns (profile_names_written, skipped_account_aliases,
    conflicting_profile_names, config_path). Makes a `.bak` backup of the
    existing config before writing (skipped entirely in dry-run mode,
    since nothing is written).

    A profile name is a "conflict" (and left completely untouched) when a
    section of that name already exists in ~/.aws/config but doesn't carry
    this tool's managed-section marker — i.e. it predates orgctl or was
    hand-edited, not something orgctl itself wrote on an earlier run.
    """
    path = aws_config_path()
    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path)

    desired, skipped = _managed_profiles_for(cfg, prefix, all_roles)

    written = []
    conflicts = []
    for name, settings in desired.items():
        section = f"profile {name}"
        if parser.has_section(section) and not parser.has_option(section, _MANAGED_KEY):
            # Pre-existing, not ours — never touch it.
            conflicts.append(name)
            continue
        if not parser.has_section(section):
            parser.add_section(section)
        for key, value in settings.items():
            parser.set(section, key, value)
        parser.set(section, _MANAGED_KEY, "true")
        written.append(name)

    if not dry_run and written:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copyfile(path, path.with_suffix(path.suffix + ".bak"))
        with path.open("w") as f:
            parser.write(f)

    return written, skipped, conflicts, path
