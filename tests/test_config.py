from __future__ import annotations

from pathlib import Path

import pytest

from stock_agent.config import ConfigError, REQUIRED_ENV_KEYS, load_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


BASE_ENV = {
    "STOCK_AGENT_DATA_DIR": "./data",
    "STOCK_AGENT_REPORT_TIMEZONE": "Asia/Seoul",
    "STOCK_AGENT_UNIVERSE_PATH": "./configs/universe.yaml",
    "STOCK_AGENT_MODELS_PATH": "./configs/models.yaml",
    "STOCK_AGENT_OBJECT_STORAGE_BUCKET": "stock-research-agent-dev",
    "STOCK_AGENT_PAPER_TRADING_ENABLED": "false",
}


def test_load_config_from_required_environment() -> None:
    config = load_config(BASE_ENV, project_root=PROJECT_ROOT)

    assert config.data_dir == PROJECT_ROOT / "data"
    assert config.report_timezone == "Asia/Seoul"
    assert config.universe_path == PROJECT_ROOT / "configs/universe.yaml"
    assert config.models_path == PROJECT_ROOT / "configs/models.yaml"
    assert config.object_storage_bucket == "stock-research-agent-dev"
    assert config.paper_trading_enabled is False


def test_missing_required_environment_variables_fail_with_readable_error() -> None:
    env = BASE_ENV.copy()
    env.pop("STOCK_AGENT_DATA_DIR")
    env["STOCK_AGENT_MODELS_PATH"] = ""

    with pytest.raises(ConfigError) as error:
        load_config(env, project_root=PROJECT_ROOT)

    message = str(error.value)
    assert "Missing required environment variables" in message
    assert "STOCK_AGENT_DATA_DIR" in message
    assert "STOCK_AGENT_MODELS_PATH" in message


def test_env_example_keys_match_loader() -> None:
    example_path = PROJECT_ROOT / ".env.example"
    keys = {
        line.split("=", 1)[0]
        for line in example_path.read_text().splitlines()
        if line and not line.startswith("#")
    }

    assert keys == set(REQUIRED_ENV_KEYS)


def test_invalid_bool_fails_with_readable_error() -> None:
    env = BASE_ENV | {"STOCK_AGENT_PAPER_TRADING_ENABLED": "maybe"}

    with pytest.raises(ConfigError, match="PAPER_TRADING_ENABLED"):
        load_config(env, project_root=PROJECT_ROOT)


def test_invalid_timezone_fails_with_readable_error() -> None:
    env = BASE_ENV | {"STOCK_AGENT_REPORT_TIMEZONE": "Not/AZone"}

    with pytest.raises(ConfigError, match="Invalid STOCK_AGENT_REPORT_TIMEZONE"):
        load_config(env, project_root=PROJECT_ROOT)
