"""Configuration management for neo."""
import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import toml

DEFAULT_CONFIG: Dict[str, Any] = {
    "sudo": {
        "method": "store",  # "prompt" or "store"
        "password": base64.b64encode(b"kdekde").decode("utf-8"),
    },
    "backends": {
        "default": "ebuild",
        "enabled": ["ebuild", "flatp", "brew", "cask", "ebins"],
    },
    "paths": {
        "brew_prefix": "/home/linuxbrew/.linuxbrew",
        "cache_dir": "~/.cache/neo",
    },
}

def get_config_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        path = Path(xdg_config) / "neo"
    else:
        path = Path.home() / ".config" / "neo"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_path() -> Path:
    return get_config_dir() / "config.toml"

def load_config() -> Dict[str, Any]:
    config_file = get_config_path()
    if not config_file.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        data = toml.load(str(config_file))
        # Ensure default keys are present
        merged = DEFAULT_CONFIG.copy()
        for section, values in data.items():
            if isinstance(values, dict) and section in merged:
                merged[section].update(values)
            else:
                merged[section] = values
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]) -> None:
    config_file = get_config_path()
    with open(config_file, "w", encoding="utf-8") as f:
        toml.dump(config_data, f)

def get_sudo_method() -> str:
    cfg = load_config()
    return cfg.get("sudo", {}).get("method", "prompt")

def get_sudo_password() -> Optional[str]:
    cfg = load_config()
    sudo_sec = cfg.get("sudo", {})
    method = sudo_sec.get("method", "prompt")
    if method == "store":
        encoded = sudo_sec.get("password")
        if encoded:
            try:
                return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
            except Exception:
                return None
    return None

def set_sudo_password(password: str, store: bool = True) -> None:
    cfg = load_config()
    if "sudo" not in cfg:
        cfg["sudo"] = {}
    if store:
        cfg["sudo"]["method"] = "store"
        cfg["sudo"]["password"] = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    else:
        cfg["sudo"]["method"] = "prompt"
        cfg["sudo"].pop("password", None)
    save_config(cfg)

def get_default_backend() -> str:
    cfg = load_config()
    return cfg.get("backends", {}).get("default", "ebuild")

def get_enabled_backends() -> List[str]:
    cfg = load_config()
    return cfg.get("backends", {}).get("enabled", ["ebuild", "flatp", "brew", "cask", "ebins"])

def get_brew_prefix() -> str:
    cfg = load_config()
    return os.path.expanduser(cfg.get("paths", {}).get("brew_prefix", "/home/linuxbrew/.linuxbrew"))

def get_cache_dir() -> Path:
    cfg = load_config()
    raw = cfg.get("paths", {}).get("cache_dir", "~/.cache/neo")
    p = Path(os.path.expanduser(raw))
    p.mkdir(parents=True, exist_ok=True)
    return p
