import configparser
from pathlib import Path

import pytest

from orgctl import aws_config_sync
from orgctl.config import Account, OrgConfig


def _cfg(**accounts: Account) -> OrgConfig:
    return OrgConfig(
        name="test",
        sso_start_url="https://example.awsapps.com/start",
        sso_region="us-east-1",
        default_region="us-east-1",
        accounts=accounts,
    )


@pytest.fixture(autouse=True)
def _fake_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_writes_new_profile_from_scratch(tmp_path):
    cfg = _cfg(prod=Account(alias="prod", account_id="111111111111", roles=["read-only"]))
    written, skipped, conflicts, path = aws_config_sync.sync(cfg)

    assert written == ["prod"]
    assert skipped == []
    assert conflicts == []
    assert path.exists()

    parser = configparser.ConfigParser()
    parser.read(path)
    assert parser.get("profile prod", "credential_process") == (
        "orgctl creds-process --account prod --role read-only"
    )


def test_rerun_overwrites_its_own_previously_written_section(tmp_path):
    cfg = _cfg(prod=Account(alias="prod", account_id="111111111111", roles=["read-only"]))
    aws_config_sync.sync(cfg)

    # Change the registry (e.g. a different role) and sync again.
    cfg2 = _cfg(prod=Account(alias="prod", account_id="111111111111", roles=["admin"]))
    written, skipped, conflicts, path = aws_config_sync.sync(cfg2)

    assert written == ["prod"]
    assert conflicts == []
    parser = configparser.ConfigParser()
    parser.read(path)
    assert "admin" in parser.get("profile prod", "credential_process")


def test_preexisting_unmanaged_profile_is_left_untouched(tmp_path):
    # Simulate a profile the user already had, e.g. from `aws configure`,
    # that happens to share a name with an orgctl account alias.
    path = tmp_path / ".aws" / "config"
    path.parent.mkdir(parents=True)
    path.write_text("[profile prod]\naws_access_key_id = AKIAEXAMPLE\nregion = us-west-2\n")

    cfg = _cfg(prod=Account(alias="prod", account_id="111111111111", roles=["read-only"]))
    written, skipped, conflicts, returned_path = aws_config_sync.sync(cfg)

    assert written == []
    assert conflicts == ["prod"]

    # File must be byte-for-byte untouched — no backup, no rewrite.
    assert returned_path.read_text() == (
        "[profile prod]\naws_access_key_id = AKIAEXAMPLE\nregion = us-west-2\n"
    )
    assert not returned_path.with_suffix(".bak").exists()


def test_dry_run_writes_nothing(tmp_path):
    cfg = _cfg(prod=Account(alias="prod", account_id="111111111111", roles=["read-only"]))
    written, skipped, conflicts, path = aws_config_sync.sync(cfg, dry_run=True)

    assert written == ["prod"]
    assert not path.exists()


def test_skips_account_with_multiple_roles_and_no_default(tmp_path):
    cfg = _cfg(
        prod=Account(alias="prod", account_id="111111111111", roles=["read-only", "admin"])
    )
    written, skipped, conflicts, path = aws_config_sync.sync(cfg)

    assert written == []
    assert skipped == ["prod"]
