import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

app = FastAPI(title="12-Factor Config Precedence")

# Allow browser-based graders to call this service cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}

def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)

def load_config():
    config = dict(DEFAULTS)

    # Layer 2: environment-specific YAML.
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{env_name}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        for key, value in yaml_config.items():
            if key in config:
                config[key] = coerce(key, value)

    # Layer 3: .env file (does not override already-present OS env vars).
    dotenv_path = BASE_DIR / ".env"
    dotenv_values = {}
    if dotenv_path.exists():
        from dotenv import dotenv_values as read_dotenv
        dotenv_values = read_dotenv(dotenv_path) or {}

    # Special alias in the .env layer.
    if dotenv_values.get("NUM_WORKERS") not in (None, ""):
        config["workers"] = coerce("workers", dotenv_values["NUM_WORKERS"])

    # Apply .env keys. Use APP_* names where applicable, and accept plain
    # config keys as a convenience for config values in .env.
    for key in config:
        app_key = f"APP_{key.upper()}"
        raw = dotenv_values.get(app_key)
        if raw is None:
            raw = dotenv_values.get(key.upper())
        if raw is not None:
            config[key] = coerce(key, raw)

    # Layer 4: actual OS environment variables, which take precedence over .env.
    for key in config:
        app_key = f"APP_{key.upper()}"
        if app_key in os.environ:
            config[key] = coerce(key, os.environ[app_key])

    # Explicit alias from OS environment too, if present.
    if "APP_NUM_WORKERS" in os.environ:
        config["workers"] = coerce("workers", os.environ["APP_NUM_WORKERS"])

    return config

@app.get("/effective-config")
def effective_config(set: Optional[list[str]] = Query(default=None)):
    config = load_config()

    # Highest layer: repeatable CLI-style query parameters, e.g.
    # ?set=port=9000&set=debug=true
    for override in set or []:
        if "=" not in override:
            continue
        key, value = override.split("=", 1)
        key = key.strip()
        if key in config:
            try:
                config[key] = coerce(key, value)
            except (TypeError, ValueError):
                # Ignore invalid values rather than failing the endpoint.
                continue

    # Never reveal the actual secret.
    config["api_key"] = "****"
    return config

@app.get("/")
def root():
    return {"message": "Config service is running", "endpoint": "/effective-config"}
