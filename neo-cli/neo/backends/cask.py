"""Homebrew Cask (:cask) backend implementation."""
from typing import Any, Callable, Dict, List, Optional
from neo.backends.brew import BrewBackend
from neo.utils import run_command

try:
    import neo_core
except ImportError:
    neo_core = None

class CaskBackend(BrewBackend):
    name = "Homebrew Cask"
    alias = "cask"

    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} install --cask {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def remove(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} uninstall --cask {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        if neo_core is not None:
            try:
                res = neo_core.search_package(query, "cask")
                if res:
                    return res
            except Exception:
                pass

        results: List[Dict[str, Any]] = []
        cmd = f"{self._get_brew_cmd()} search --cask {query}"
        ret, out = run_command(cmd, sudo=False, print_output=False)
        if ret == 0:
            for line in out.splitlines():
                line = line.strip()
                if not line or line.startswith("==>") or "==>" in line:
                    continue
                for pkg in line.split():
                    results.append({
                        "name": pkg,
                        "version": "latest",
                        "description": "Homebrew Cask application",
                        "backend": self.alias,
                        "installed": False,
                    })
        return results

    def list_installed(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not self.is_available():
            return results

        cmd = f"{self._get_brew_cmd()} list --cask --versions"
        ret, out = run_command(cmd, sudo=False, print_output=False)
        if ret == 0:
            for line in out.splitlines():
                parts = line.split()
                if parts:
                    name = parts[0]
                    ver = parts[1] if len(parts) > 1 else "installed"
                    results.append({
                        "name": name,
                        "version": ver,
                        "description": "Homebrew Cask application",
                        "backend": self.alias,
                        "installed": True,
                    })
        return results

    def info(self, package: str) -> Dict[str, Any]:
        info_data = {
            "name": package,
            "backend": self.alias,
            "version": "unknown",
            "description": "",
            "homepage": "",
            "installed": False,
        }
        if not self.is_available():
            return info_data

        cmd = f"{self._get_brew_cmd()} info --cask --json=v2 {package}"
        ret, out = run_command(cmd, sudo=False, print_output=False)
        if ret == 0:
            import json
            try:
                parsed = json.loads(out)
                casks = parsed.get("casks", [])
                if casks:
                    c = casks[0]
                    info_data["version"] = c.get("version", "unknown")
                    info_data["description"] = c.get("desc", "")
                    info_data["homepage"] = c.get("homepage", "")
                    info_data["installed"] = bool(c.get("installed"))
            except Exception:
                pass
        info_data["raw"] = out
        return info_data

    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} upgrade --cask"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0
