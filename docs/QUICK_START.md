# Quick Start

## 1. Install

```bash
git clone https://github.com/DustyStudy/aws-orgctl.git
cd aws-orgctl
python3 -m pip install -e .
```

## 2. Set up your account registry

```bash
orgctl init
```

This copies the bundled `orgs.example.yaml` (kept in sync with
[`config/orgs.example.yaml`](../config/orgs.example.yaml) in this repo) to
`~/.orgctl/orgs.yaml`. Open it and fill in:

- `sso_start_url` — your IAM Identity Center portal URL (looks like
  `https://<your-subdomain>.awsapps.com/start`)
- `sso_region` — the region your Identity Center instance is deployed in
- `accounts` — an alias per account you use, its 12-digit account ID, and
  the permission-set/role names you're assigned there

## 3. Verify

```bash
orgctl doctor
```

Confirms your config parses and the local cache directory is writable.

## 4. Log in

```bash
orgctl login
```

Opens your browser to approve a device-authorization request — the same
flow `aws sso login` uses. The resulting token is cached locally
(`~/.orgctl/cache`) until it naturally expires (typically ~8 hours).

## 5. Use it

```bash
# One-off command
orgctl exec -a prod -r read-only -- aws s3 ls

# Interactive session
orgctl shell -a prod -r read-only

# What am I actually granted right now?
orgctl list-remote

# Review recent activity
orgctl audit-log

# Done for the day
orgctl logout
```

## Optional: guardrails

Copy `config/guardrails.example.yaml` to `~/.orgctl/guardrails.yaml` and
adjust the protected-account list and deny/confirm patterns for your own
environment.
