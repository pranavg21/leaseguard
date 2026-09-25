"""Runtime settings read from environment variables. No secrets live in code."""

import os
from dataclasses import dataclass

DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class Settings:
    """Settings resolved from the environment.

    Attributes:
        gemini_api_key: API key for Gemini, or None to run offline.
        gemini_model: Gemini model name.
        firestore_collection: Firestore collection for anonymous metrics, or None.
    """

    gemini_api_key: str | None
    gemini_model: str
    firestore_collection: str | None

    @property
    def llm_enabled(self) -> bool:
        """Whether a Gemini key is configured."""
        return bool(self.gemini_api_key)


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def get_settings() -> Settings:
    """Read settings from the environment (see ``.env.example``).

    Returns:
        The current settings.
    """
    return Settings(
        gemini_api_key=_env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY"),
        gemini_model=_env("GEMINI_MODEL") or DEFAULT_MODEL,
        firestore_collection=_env("FIRESTORE_COLLECTION"),
    )
