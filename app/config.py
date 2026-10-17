"""Environment configuration. Values come only from env vars (or a local, gitignored .env)."""

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    api_url: str
    api_key: str
    model_name: str
    mock_mode: bool

    @property
    def endpoint_host(self) -> str:
        from urllib.parse import urlparse

        return urlparse(self.api_url).hostname or "<unset>"


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader for local dev. Real environment variables always win."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_DEFAULT_DOTENV = object()


def load_settings(dotenv_path=_DEFAULT_DOTENV) -> Settings:
    """dotenv_path=None reads no .env file. By default reads $SHELF_SENSE_DOTENV or <repo>/.env."""
    if dotenv_path is _DEFAULT_DOTENV:
        dotenv_path = Path(os.environ.get("SHELF_SENSE_DOTENV", REPO_ROOT / ".env"))
    if dotenv_path is not None:
        _load_dotenv(dotenv_path)

    mock_mode = os.environ.get("MOCK_MODE", "false").strip().lower() in {"1", "true", "yes"}
    settings = Settings(
        api_url=os.environ.get("AMD_API_URL", "").strip().rstrip("/"),
        api_key=os.environ.get("AMD_API_KEY", "").strip(),
        model_name=os.environ.get("MODEL_NAME", "").strip(),
        mock_mode=mock_mode,
    )

    if not mock_mode:
        missing = [
            name
            for name, value in (("AMD_API_URL", settings.api_url), ("MODEL_NAME", settings.model_name))
            if not value or "<" in value
        ]
        if missing:
            raise ConfigError(
                f"Missing or placeholder config: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in the AMD Token Factory values."
            )
    return settings
