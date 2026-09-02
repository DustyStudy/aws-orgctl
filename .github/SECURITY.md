# Security Policy

## Reporting a vulnerability

If you find a security issue in `orgctl`, please open a private report via
GitHub's **Security → Report a vulnerability** on this repo rather than a
public issue. If that's unavailable, open an issue with minimal detail
asking for a private channel and it'll be picked up from there.

## Scope

`orgctl` handles short-lived AWS credentials. Areas that get the most
scrutiny for security review:

- `src/orgctl/sso.py` — the device-authorization flow and token handling
- `src/orgctl/cache.py` — where tokens and role credentials are persisted
  (OS keychain when available, 0600 local files otherwise)
- `src/orgctl/exec_cmd.py` — how credentials are exported into child
  processes
- `src/orgctl/guardrails.py` — the local deny/confirm-pattern checks

## Design notes relevant to security review

- No code path accepts, stores, or exports a long-lived IAM access key —
  everything comes from AWS SSO's `GetRoleCredentials`, which is inherently
  short-lived.
- Cached credentials live in the OS keychain (SSO tokens, when the
  `keyring` extra is installed and a backend is available) or in
  owner-only (0600) local files, with expiry checked on every read.
- Guardrails (`guardrails.yaml`) and the IAM policy pre-check
  (`check-policy`, `--check-action`) are explicitly **not** a security
  boundary — they're local, best-effort speed bumps. Real enforcement
  belongs in IAM permission boundaries and Service Control Policies. Both
  the code and the README say so; please flag it if you find a place where
  the tool implies otherwise.
- The local audit log (`~/.orgctl/audit.log`) and any `--reason` text are
  never transmitted anywhere by this tool except when you explicitly run
  `orgctl audit-log --push-cloudwatch`.

## Supported versions

Pre-1.0 — only the latest `main` is supported. Once there's a first
tagged release, this section will be updated with a version table.
