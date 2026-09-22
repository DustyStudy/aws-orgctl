import os
import subprocess
import sys
import time

import pytest

from orgctl import cache, sso

START_URL = "https://example.awsapps.com/start"
REGION = "us-east-1"


def _key_in_subprocess(hash_seed: str) -> str:
    code = f"from orgctl import sso; print(sso._token_cache_key({START_URL!r}, {REGION!r}))"
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def test_token_cache_key_is_stable_across_processes():
    # Regression: the key used the builtin hash(), which is randomized per
    # process, so a token cached by one invocation was never found by the next.
    keys = {_key_in_subprocess(seed) for seed in ("1", "2", "3")}
    assert len(keys) == 1


def test_token_cache_key_differs_per_start_url_and_region():
    a = sso._token_cache_key("https://a.awsapps.com/start", REGION)
    b = sso._token_cache_key("https://b.awsapps.com/start", REGION)
    c = sso._token_cache_key("https://a.awsapps.com/start", "eu-west-1")
    assert len({a, b, c}) == 3


def test_token_cache_key_is_filename_safe():
    key = sso._token_cache_key(START_URL, REGION)
    assert all(ch.isalnum() or ch in "-_" for ch in key)


def test_login_reuses_cached_token_without_calling_aws(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    now = time.time()
    cache.put(
        sso._token_cache_key(START_URL, REGION),
        {"accessToken": "cached-token", "expiresAt": now + 3600, "issuedAt": now},
    )

    def _no_aws(*args, **kwargs):
        raise AssertionError("login() should have used the cached token, not called AWS")

    monkeypatch.setattr(sso.boto3, "client", _no_aws)

    token = sso.login(START_URL, REGION, open_browser=False)
    assert token.access_token == "cached-token"


def test_login_ignores_cached_token_older_than_max_session(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGCTL_HOME", str(tmp_path))
    now = time.time()
    key = sso._token_cache_key(START_URL, REGION)
    cache.put(
        key,
        {"accessToken": "old", "expiresAt": now + 3600, "issuedAt": now - 10 * 3600},
    )

    class _StopHere(Exception):
        pass

    def _fresh_login_attempted(*args, **kwargs):
        raise _StopHere

    monkeypatch.setattr(sso.boto3, "client", _fresh_login_attempted)

    with pytest.raises(_StopHere):
        sso.login(START_URL, REGION, open_browser=False, max_session_hours=8)
    assert cache.get(key) is None
