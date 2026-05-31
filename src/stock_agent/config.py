from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    report_timezone: str
    universe_path: Path
    models_path: Path
    object_storage_bucket: str
    paper_trading_enabled: bool


REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "STOCK_AGENT_DATA_DIR",
    "STOCK_AGENT_REPORT_TIMEZONE",
    "STOCK_AGENT_UNIVERSE_PATH",
    "STOCK_AGENT_MODELS_PATH",
    "STOCK_AGENT_OBJECT_STORAGE_BUCKET",
    "STOCK_AGENT_PAPER_TRADING_ENABLED",
)


def load_config(
    env: Mapping[str, str] | None = None,
    project_root: Path | None = None,
) -> AppConfig:
    source = os.environ if env is None else env
    root = Path.cwd() if project_root is None else Path(project_root)

    missing = [key for key in REQUIRED_ENV_KEYS if not source.get(key, "").strip()]
    if missing:
        names = ", ".join(missing)
        raise ConfigError(f"Missing required environment variables: {names}")

    report_timezone = source["STOCK_AGENT_REPORT_TIMEZONE"].strip()
    _validate_timezone(report_timezone)

    bucket = source["STOCK_AGENT_OBJECT_STORAGE_BUCKET"].strip()
    if any(char.isspace() for char in bucket):
        raise ConfigError("STOCK_AGENT_OBJECT_STORAGE_BUCKET must not contain whitespace")

    return AppConfig(
        data_dir=_resolve_path(source["STOCK_AGENT_DATA_DIR"], root),
        report_timezone=report_timezone,
        universe_path=_resolve_path(source["STOCK_AGENT_UNIVERSE_PATH"], root),
        models_path=_resolve_path(source["STOCK_AGENT_MODELS_PATH"], root),
        object_storage_bucket=bucket,
        paper_trading_enabled=_parse_bool(source["STOCK_AGENT_PAPER_TRADING_ENABLED"]),
    )


def _resolve_path(value: str, project_root: Path) -> Path:
    path = Path(value.strip()).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigError(
        "STOCK_AGENT_PAPER_TRADING_ENABLED must be one of true/false, yes/no, on/off, or 1/0"
    )


def _validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ConfigError(f"Invalid STOCK_AGENT_REPORT_TIMEZONE: {value}") from exc
