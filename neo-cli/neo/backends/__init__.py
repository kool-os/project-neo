"""Backend registry and factory for neo."""
from typing import Dict, List, Optional
from neo.backends.base import Backend
from neo.backends.ebuild import EbuildBackend
from neo.backends.flatpak import FlatpakBackend
from neo.backends.brew import BrewBackend
from neo.backends.cask import CaskBackend
from neo.backends.ebins import EbinsBackend
from neo.config import get_default_backend, get_enabled_backends

BACKEND_CLASSES = {
    "ebuild": EbuildBackend,
    "flatp": FlatpakBackend,
    "brew": BrewBackend,
    "cask": CaskBackend,
    "ebins": EbinsBackend,
}

_BACKEND_INSTANCES: Dict[str, Backend] = {}

def get_backend(alias: str) -> Optional[Backend]:
    """Get an initialized Backend instance by alias (ebuild, flatp, brew, cask, ebins)."""
    norm = alias.strip().lower()
    if norm.startswith(":"):
        norm = norm[1:]

    # Map aliases
    alias_map = {
        "ebuild": "ebuild",
        "portage": "ebuild",
        "flatp": "flatp",
        "flatpak": "flatp",
        "brew": "brew",
        "homebrew": "brew",
        "cask": "cask",
        "ebins": "ebins",
        "binpkg": "ebins",
    }
    canonical = alias_map.get(norm, norm)

    if canonical not in BACKEND_CLASSES:
        return None

    if canonical not in _BACKEND_INSTANCES:
        _BACKEND_INSTANCES[canonical] = BACKEND_CLASSES[canonical]()
    return _BACKEND_INSTANCES[canonical]

def get_all_backends() -> Dict[str, Backend]:
    """Get instances of all backends."""
    for alias in BACKEND_CLASSES:
        if alias not in _BACKEND_INSTANCES:
            _BACKEND_INSTANCES[alias] = BACKEND_CLASSES[alias]()
    return _BACKEND_INSTANCES.copy()

def get_available_backends() -> Dict[str, Backend]:
    """Get instances of backends whose underlying tools are installed on this system."""
    all_b = get_all_backends()
    return {alias: b for alias, b in all_b.items() if b.is_available()}

def resolve_backend(alias: Optional[str] = None) -> Backend:
    """Resolve backend from explicit alias or system default/auto-detection."""
    if alias:
        b = get_backend(alias)
        if b:
            return b

    # Try default backend from config
    def_alias = get_default_backend()
    b = get_backend(def_alias)
    if b and b.is_available():
        return b

    # Auto-detect any available enabled backend
    avail = get_available_backends()
    enabled = get_enabled_backends()
    for en in enabled:
        if en in avail:
            return avail[en]

    # Fallback to ebuild
    return get_backend("ebuild") or EbuildBackend()
