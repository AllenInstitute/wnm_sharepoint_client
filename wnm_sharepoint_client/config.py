import json
import os

REQUIRED_AUTH_KEYS = {
    "CLIENT_ID",
    "TENANT_ID",
    "CLIENT_SECRET",
    "SCOPE",
    "GRAPH_API_BASE_URL",
    "TOP",
}
REQUIRED_SITE_KEYS = {"SITE_ID", "DRIVE_ID", "SITE_URL"}


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


config_path = os.getenv("CONFIG_JSON_PATH")
if config_path:
    if not os.path.isfile(config_path):
        raise ConfigError(
            f"CONFIG_JSON_PATH is set but file does not exist: {config_path}"
        )

    with open(config_path, "r") as f:
        SITE_MANAGER = json.load(f)

    if len(SITE_MANAGER) == 0:
        raise ConfigError(
            f"config.json file at {config_path} was found but no variables were loaded."
        )

    if "auth" not in SITE_MANAGER:
        raise ConfigError(
            "Missing 'auth' data in config. Please see example_config.json"
        )

    if "sites" not in SITE_MANAGER:
        raise ConfigError(
            "Missing 'sites' section in config. Please see example_config.json"
        )

    missing_auth_keys = REQUIRED_AUTH_KEYS - set(SITE_MANAGER["auth"].keys())
    if missing_auth_keys:
        raise ConfigError(f"Missing auth keys: {', '.join(missing_auth_keys)}")

    for site_key, site_data in SITE_MANAGER["sites"].items():
        missing_site_keys = REQUIRED_SITE_KEYS - set(site_data.keys())
        if missing_site_keys:
            raise ConfigError(
                f"Missing keys in site '{site_key}': {', '.join(missing_site_keys)}"
            )


else:
    raise ConfigError(f"CONFIG_JSON_PATH must be set as an environment variable")
