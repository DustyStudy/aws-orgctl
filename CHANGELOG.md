# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); once tagged
releases start, versioning follows [SemVer](https://semver.org/).

Entries below `[Unreleased]` are managed automatically by
[release-please](https://github.com/googleapis/release-please) once that
workflow is active (see `.github/workflows/release-please.yml`) — it opens
a PR that moves these into a versioned section on each release. Until the
first tag exists, this file is maintained by hand.

## [Unreleased]

### Added
- Initial `orgctl` CLI: `init`, `login`, `logout`, `doctor`, `accounts`,
  `list-remote`, `exec`, `shell`, `creds-process`, `whoami`, `check-policy`,
  `completion`, `audit-log`.
- IAM Identity Center (AWS SSO) device-authorization login flow.
- Local account/role registry (`orgs.yaml`).
- Local guardrails (`guardrails.yaml`) — deny-patterns, protected accounts,
  require-confirmation patterns, with sensible built-in defaults.
- Local JSONL audit log, with optional `--reason` justification and
  optional CloudWatch Logs export (`audit-log --push-cloudwatch`).
- Native `credential_process` support (`creds-process`) for use with plain
  `--profile` in the AWS CLI/SDKs/Terraform.
- `sync-aws-config` — writes/updates `credential_process` profiles in
  `~/.aws/config` for every account (or account/role with `--all-roles`)
  in the registry, without touching unrelated profiles.
- Advisory IAM policy pre-check (`check-policy`, `--check-action` on
  `exec`) via `iam:SimulatePrincipalPolicy` (identity-based policies only —
  does not evaluate SCPs or resource policies).
- Configurable local session cap (`max_session_hours`) independent of the
  SSO token's own server-side expiry.
- OS-keychain storage for SSO tokens via the optional `keyring` extra, with
  automatic fallback to the existing 0600 file-based cache.
- `--json` output on `accounts`, `list-remote`, and `audit-log`.
- `export-env` — prints export/`$env:` lines for the current shell, as an
  alternative to spawning a subshell via `shell`.
- Session-expiry heads-up in `shell` when credentials have under 15
  minutes left.
- CI: ruff lint + format, mypy, pytest (Python 3.11/3.12).
- Dependabot (pip + GitHub Actions), pre-commit config, CODEOWNERS,
  CONTRIBUTING.md, SECURITY.md.
