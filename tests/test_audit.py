from orgctl import audit


def test_record_and_tail(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    audit.record(
        action="exec", account_id="123456789012", role="admin", command=["aws", "s3", "ls"]
    )
    entries = audit.tail(5)
    assert len(entries) == 1
    assert entries[0]["action"] == "exec"
    assert entries[0]["account_id"] == "123456789012"
    assert entries[0]["command"] == ["aws", "s3", "ls"]
    assert entries[0]["reason"] is None


def test_record_with_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    audit.record(action="shell", account_id="999", role="read-only", reason="JIRA-42")
    entries = audit.tail(5)
    assert entries[0]["reason"] == "JIRA-42"


def test_tail_returns_empty_when_no_log(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    assert audit.tail(10) == []


def test_tail_respects_n(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    for i in range(5):
        audit.record(action="exec", account_id=str(i), role="r")
    entries = audit.tail(2)
    assert len(entries) == 2
    assert entries[-1]["account_id"] == "4"
