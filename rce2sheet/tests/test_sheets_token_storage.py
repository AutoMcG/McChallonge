import pytest
import rce2sheet.sheets as sheets


class FakeKeyring:
    def __init__(self):
        self._store = {}

    def get_password(self, service_name, username):
        return self._store.get((service_name, username))

    def set_password(self, service_name, username, password):
        self._store[(service_name, username)] = password


def test_load_oauth_token_prefers_keyring(monkeypatch, tmp_path):
    token_path = str(tmp_path / "token.json")
    fake_keyring = FakeKeyring()
    fake_keyring.set_password(sheets.TOKEN_SERVICE_NAME, token_path, '{"token":"abc"}')

    monkeypatch.setattr(sheets, "keyring", fake_keyring)
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    loaded = sheets._load_oauth_token(token_path)
    assert loaded == '{"token":"abc"}'


def test_load_oauth_token_migrates_legacy_file_to_keyring(monkeypatch, tmp_path):
    token_file = tmp_path / "legacy_token.json"
    token_file.write_text('{"token":"from-file"}', encoding="utf-8")

    fake_keyring = FakeKeyring()
    monkeypatch.setattr(sheets, "keyring", fake_keyring)
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    loaded = sheets._load_oauth_token(str(token_file))

    assert loaded == '{"token":"from-file"}'
    assert (
        fake_keyring.get_password(sheets.TOKEN_SERVICE_NAME, str(token_file))
        == '{"token":"from-file"}'
    )


def test_save_oauth_token_falls_back_to_file_when_keyring_write_fails(
    monkeypatch, tmp_path
):
    token_file = tmp_path / "fallback_token.json"

    class BrokenKeyring:
        def set_password(self, *_args, **_kwargs):
            raise RuntimeError("no keyring backend")

    monkeypatch.setattr(sheets, "keyring", BrokenKeyring())
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    sheets._save_oauth_token(str(token_file), '{"token":"saved-to-file"}')

    assert token_file.read_text(encoding="utf-8") == '{"token":"saved-to-file"}'


def test_build_service_raises_without_client_secrets_when_no_token(
    monkeypatch, tmp_path
):
    """client_secrets_path=None raises a clear error when no token is stored."""
    monkeypatch.setattr(sheets, "_load_oauth_token", lambda _path: None)

    with pytest.raises(RuntimeError, match="--oauth-client-secrets"):
        sheets._build_service_from_user_oauth(None, str(tmp_path / "no_token.json"))
    def __init__(self):
        self._store = {}

    def get_password(self, service_name, username):
        return self._store.get((service_name, username))

    def set_password(self, service_name, username, password):
        self._store[(service_name, username)] = password


def test_load_oauth_token_prefers_keyring(monkeypatch, tmp_path):
    token_path = str(tmp_path / "token.json")
    fake_keyring = FakeKeyring()
    fake_keyring.set_password(sheets.TOKEN_SERVICE_NAME, token_path, '{"token":"abc"}')

    monkeypatch.setattr(sheets, "keyring", fake_keyring)
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    loaded = sheets._load_oauth_token(token_path)
    assert loaded == '{"token":"abc"}'


def test_load_oauth_token_migrates_legacy_file_to_keyring(monkeypatch, tmp_path):
    token_file = tmp_path / "legacy_token.json"
    token_file.write_text('{"token":"from-file"}', encoding="utf-8")

    fake_keyring = FakeKeyring()
    monkeypatch.setattr(sheets, "keyring", fake_keyring)
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    loaded = sheets._load_oauth_token(str(token_file))

    assert loaded == '{"token":"from-file"}'
    assert (
        fake_keyring.get_password(sheets.TOKEN_SERVICE_NAME, str(token_file))
        == '{"token":"from-file"}'
    )


def test_save_oauth_token_falls_back_to_file_when_keyring_write_fails(
    monkeypatch, tmp_path
):
    token_file = tmp_path / "fallback_token.json"

    class BrokenKeyring:
        def set_password(self, *_args, **_kwargs):
            raise RuntimeError("no keyring backend")

    monkeypatch.setattr(sheets, "keyring", BrokenKeyring())
    monkeypatch.setenv("RCE2SHEET_TOKEN_BACKEND", "keyring")

    sheets._save_oauth_token(str(token_file), '{"token":"saved-to-file"}')

    assert token_file.read_text(encoding="utf-8") == '{"token":"saved-to-file"}'
