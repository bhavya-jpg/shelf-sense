import pytest

from app.config import ConfigError, load_settings

VARS = ("AMD_API_URL", "AMD_API_KEY", "MODEL_NAME", "MOCK_MODE")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in VARS:
        monkeypatch.delenv(v, raising=False)


def test_missing_values_raise_without_mock(monkeypatch):
    with pytest.raises(ConfigError, match="AMD_API_URL, MODEL_NAME"):
        load_settings(dotenv_path=None)


def test_placeholder_values_are_rejected(monkeypatch):
    monkeypatch.setenv("AMD_API_URL", "https://<token-factory-endpoint>/v1")
    monkeypatch.setenv("MODEL_NAME", "<confirmed-vision-model-name-from-milestone-0>")
    with pytest.raises(ConfigError):
        load_settings(dotenv_path=None)


def test_real_values_load_and_trailing_slash_is_stripped(monkeypatch):
    monkeypatch.setenv("AMD_API_URL", "https://example.test/v1/")
    monkeypatch.setenv("MODEL_NAME", "some-vlm")
    s = load_settings(dotenv_path=None)
    assert s.api_url == "https://example.test/v1" and s.endpoint_host == "example.test"
    assert s.mock_mode is False


def test_mock_mode_needs_no_credentials(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "true")
    assert load_settings(dotenv_path=None).mock_mode is True


def test_dotenv_does_not_override_real_env(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("AMD_API_URL=https://from-file.test/v1\nMODEL_NAME=file-model\n# comment\n")
    monkeypatch.setenv("MODEL_NAME", "env-model")
    s = load_settings(dotenv_path=env)
    assert s.api_url == "https://from-file.test/v1" and s.model_name == "env-model"
