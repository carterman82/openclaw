"""Centralized env loading for the openclaw agent."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    ANTHROPIC_API_KEY: str
    WP_BASE_URL: str
    WP_USERNAME: str
    WP_APP_PASSWORD: str
    OPENAI_API_KEY: str | None = None

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()
        required = (
            "ANTHROPIC_API_KEY",
            "WP_BASE_URL",
            "WP_USERNAME",
            "WP_APP_PASSWORD",
        )
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise RuntimeError(
                f"missing required env vars: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill them in."
            )
        return cls(
            ANTHROPIC_API_KEY=os.environ["ANTHROPIC_API_KEY"],
            WP_BASE_URL=os.environ["WP_BASE_URL"].rstrip("/"),
            WP_USERNAME=os.environ["WP_USERNAME"],
            WP_APP_PASSWORD=os.environ["WP_APP_PASSWORD"],
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        )
