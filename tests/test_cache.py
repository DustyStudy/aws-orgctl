import time

from orgctl import cache


def test_put_and_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("mykey", {"value": 42, "expiresAt": time.time() + 60})
    result = cache.get("mykey")
    assert result is not None
    assert result["value"] == 42


def test_expired_entry_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("expired", {"value": 1, "expiresAt": time.time() - 10})
    assert cache.get("expired") is None


def test_missing_key_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    assert cache.get("does-not-exist") is None


def test_clear_single_key(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("a", {"value": 1, "expiresAt": time.time() + 60})
    cache.put("b", {"value": 2, "expiresAt": time.time() + 60})
    removed = cache.clear("a")
    assert removed == 1
    assert cache.get("a") is None
    assert cache.get("b") is not None


def test_clear_all(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("a", {"value": 1, "expiresAt": time.time() + 60})
    cache.put("b", {"value": 2, "expiresAt": time.time() + 60})
    removed = cache.clear()
    assert removed == 2
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_sso_token_key_roundtrips_without_keyring(tmp_path, monkeypatch):
    """sso-token_* keys attempt the OS keychain first, but must still work
    correctly (via the file-based fallback) on a system with no keyring
    backend available — e.g. this test environment, and most CI runners."""
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("sso-token_us-east-1_123", {"accessToken": "abc", "expiresAt": time.time() + 60})
    result = cache.get("sso-token_us-east-1_123")
    assert result is not None
    assert result["accessToken"] == "abc"


def test_sso_token_key_respects_expiry(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    cache.put("sso-token_expired", {"accessToken": "x", "expiresAt": time.time() - 10})
    assert cache.get("sso-token_expired") is None
