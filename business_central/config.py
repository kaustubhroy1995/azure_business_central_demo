"""Configuration loader for Business Central API credentials."""

import json
import os

REQUIRED_KEYS = ["tenant_id", "client_id", "client_secret", "environment", "company_id"]


def load_config(path: str = "config.json") -> dict:
    """Load and validate the configuration file.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        A dict with the configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If required keys are missing or empty.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Configuration file not found: {path}. "
            "Copy config.example.json to config.json and fill in your credentials."
        )

    with open(path, "r") as f:
        config = json.load(f)

    missing = [k for k in REQUIRED_KEYS if not config.get(k)]
    if missing:
        raise ValueError(
            f"Missing or empty configuration keys: {', '.join(missing)}. "
            "See config.example.json for documentation."
        )

    return config
