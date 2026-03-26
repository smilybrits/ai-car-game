"""Utility helpers for loading and validating reward configuration JSON files."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_KEYS = {
    "name",
    "time_penalty",
    "checkpoint_bonus",
    "lap_bonus",
    "speed_reward_weight",
    "collision_penalty",
    "stuck_penalty",
    "slow_penalty",
    "stuck_steps_threshold",
    "slow_speed_threshold",
    "action_threshold",
}


def load_reward_config(path: str | Path) -> dict[str, float | str]:
    """Load and validate one reward configuration JSON file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Reward config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Reward config must be a JSON object.")

    missing_keys = sorted(REQUIRED_KEYS.difference(config.keys()))
    if missing_keys:
        raise ValueError(f"Reward config is missing required keys: {', '.join(missing_keys)}")

    if not isinstance(config["name"], str) or not config["name"].strip():
        raise ValueError("Reward config 'name' must be a non-empty string.")

    validated: dict[str, float | str] = {"name": config["name"].strip()}
    for key in sorted(REQUIRED_KEYS.difference({"name"})):
        try:
            validated[key] = float(config[key])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Reward config key '{key}' must be numeric.") from error

    return validated


def load_reward_config_by_name(name: str) -> tuple[dict[str, float | str], Path]:
    """Load reward config by file name from reward_configs/<name>.json."""
    config_name = name.strip()
    if not config_name:
        raise ValueError("Reward config name cannot be empty.")

    config_path = Path("reward_configs") / f"{config_name}.json"
    return load_reward_config(config_path), config_path
