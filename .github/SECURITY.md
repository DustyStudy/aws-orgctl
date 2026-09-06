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

## CI/CD supply-chain hardening

Every workflow under `.github/workflows/` follows the same baseline:

- **Least-privilege `permissions`** declared at the workflow level
  (`contents: read` by default), with any broader permission (e.g.
  `security-events: write` for SARIF uploads, `id-token: write` for
  Scorecard's Sigstore signing) scoped to only the specific job that needs
  it — never at the workflow level.
- **`step-security/harden-runner`** as the first step of every job. It
  monitors and can restrict network egress and file/process activity on
  the runner, which is how real incidents like the `tj-actions/changed-files`
  supply-chain compromise (CVE-2025-30066) get caught in practice. Currently
  running in `audit` (log-only) mode while the egress allowlist is
  characterized; the plan is to move to `block` mode with an explicit
  allowlist once a few weeks of audit logs confirm nothing legitimate gets
  blocked.
- **`persist-credentials: false`** on every `actions/checkout` step, so the
  ephemeral `GITHUB_TOKEN` isn't left sitting in the local git config for
  the rest of the job.
- **Explicit `timeout-minutes`** on every job, so a hung or runaway step
  can't tie up compute (or a compromised dependency) indefinitely.
- **`concurrency` groups**, so superseded runs on the same ref get
  cancelled instead of piling up.

**Action pinning policy:** actions are pinned to a full commit SHA by
default (immutable — a tag like `@v4` can be moved by the maintainer, or by
an attacker who compromises the maintainer's account, without any signal to
consumers). The exceptions are first-party GitHub actions
(`actions/dependency-review-action`, `github/codeql-action`) and
`googleapis/release-please-action`, pinned to major-version tags instead —
`github/codeql-action`'s own README explicitly recommends *against*
SHA-pinning it, since some of its features are gated by server-side flags
tied to the version tag rather than the code itself. Each such exception is
called out with a comment in the workflow file where it's used.
`ossf/scorecard-action` is SHA-pinned like the default case — it doesn't
actually publish a floating major-version tag, only full `vX.Y.Z` tags, so
tag-pinning it isn't an option regardless of policy.

Dependabot (`.github/dependabot.yml`) keeps both the SHA-pinned and
tag-pinned actions current automatically.

## Supported versions

Pre-1.0 — only the latest `main` is supported. Once there's a first
tagged release, this section will be updated with a version table.
