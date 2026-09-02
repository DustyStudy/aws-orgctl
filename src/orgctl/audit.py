"""Local audit trail.

Every exec/shell invocation appends one JSON line to ~/.orgctl/audit.log.
This is a local record for your own review (e.g. "what did I run against
prod last Tuesday") — it is never uploaded anywhere by this tool.
"""

from __future__ import annotations

import getpass
import json
import os
import socket
import time
from pathlib import Path
from typing import TYPE_CHECKING


def log_path() -> Path:
    base = Path(os.environ.get("ORGCTL_HOME", Path.home() / ".orgctl"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "audit.log"


def record(
    *,
    action: str,
    account_id: str,
    role: str,
    command: list[str] | None = None,
    result: str = "ok",
    detail: str | None = None,
    reason: str | None = None,
) -> None:
    """Append one entry to the local audit log.

    `reason` is a free-text justification (e.g. a ticket number) the caller
    can pass with `--reason` on `exec`/`shell`. It's recorded locally for
    your own review only — the AWS SSO GetRoleCredentials API this tool uses
    has no session-tagging parameter, so this is NOT the same as an actual
    STS session tag attached to the credentials themselves. If you need a
    real, AWS-side session tag, that requires a direct sts:AssumeRole call
    against a role ARN instead of SSO's GetRoleCredentials.
    """
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "action": action,
        "account_id": account_id,
        "role": role,
        "command": command or [],
        "result": result,
        "detail": detail,
        "reason": reason,
    }
    with log_path().open("a") as f:
        f.write(json.dumps(entry) + "\n")


def push_to_cloudwatch(log_group: str, region: str, n: int = 100) -> int:
    """Push the last `n` local audit-log lines to a CloudWatch Logs group.

    Uses whatever credentials are already active in the calling process's
    environment (e.g. run this inside `orgctl shell` for a low-privilege
    logging role, or export creds for a role that only has logs:PutLogEvents
    / logs:CreateLogStream on this log group). Returns the number of entries
    pushed. Requires boto3 — imported lazily so the rest of this module has
    no hard AWS dependency.
    """
    import boto3

    if TYPE_CHECKING:
        from mypy_boto3_logs.type_defs import InputLogEventTypeDef

    entries = tail(n)
    if not entries:
        return 0

    client = boto3.client("logs", region_name=region)
    stream_name = f"{socket.gethostname()}-{getpass.getuser()}"

    try:
        client.create_log_stream(logGroupName=log_group, logStreamName=stream_name)
    except client.exceptions.ResourceAlreadyExistsException:
        pass

    log_events: list[InputLogEventTypeDef] = [
        {"timestamp": int(time.time() * 1000), "message": json.dumps(e)} for e in entries
    ]
    log_events.sort(key=lambda ev: ev["timestamp"])

    client.put_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        logEvents=log_events,
    )
    return len(log_events)


def tail(n: int = 20) -> list[dict]:
    p = log_path()
    if not p.exists():
        return []
    lines = p.read_text().splitlines()[-n:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
