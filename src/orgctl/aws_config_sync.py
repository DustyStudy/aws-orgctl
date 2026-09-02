"""Write `credential_process` profile blocks into ~/.aws/config for every
account (and optionally every role) in the local orgs.yaml registry.

Uses configparser so any profiles you already have — hand-written, from
`aws configure`, whatever — are preserved untouched. Only sections this
tool itself created (tagged with a marker comment) are ever overwritten on
a re-run; anything else is left exactly as-is.
"""

from __future__ import annotations

import configparser
import shutil
from pathlib import Path

from .config import Account, OrgConfig

MARKER = "# managed-by: orgctl sync-aws-config"


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
) -> tuple[list[str], list[str], Path]:
    """Write/update profiles in ~/.aws/config for every account/role.

    Returns (profile_names_written, skipped_account_aliases, config_path).
    Makes a `.bak` backup of the existing config before writing (skipped
    entirely in dry-run mode, since nothing is written).
    """
    path = aws_config_path()
    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path)

    desired, skipped = _managed_profiles_for(cfg, prefix, all_roles)

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copyfile(path, path.with_suffix(path.suffix + ".bak"))

    written = []
    for name, settings in desired.items():
        section = f"profile {name}"
        if not parser.has_section(section):
            parser.add_section(section)
        for key, value in settings.items():
            parser.set(section, key, value)
        written.append(name)

    if not dry_run:
        with path.open("w") as f:
            f.write(f"{MARKER}\n")
            parser.write(f)

    return written, skipped, path
