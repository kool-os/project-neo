"""Linuxbrew (:brew) backend implementation."""
import os
from typing import Any, Callable, Dict, List, Optional
from neo.backends.base import Backend
from neo.config import get_brew_prefix
from neo.utils import check_command_exists, run_command

try:
    import neo_core
except ImportError:
    neo_core = None

class BrewBackend(Backend):
    name = "Homebrew"
    alias = "brew"

    def _get_brew_cmd(self) -> str:
        prefix = get_brew_prefix()
        candidate = os.path.join(prefix, "bin", "brew")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        return "brew"

    def is_available(self) -> bool:
        cmd = self._get_brew_cmd()
        return check_command_exists(cmd)

    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} install {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def remove(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} uninstall {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        if neo_core is not None:
            try:
                res = neo_core.search_package(query, "brew")
                if res:
                    return res
            except Exception:
                pass

        results: List[Dict[str, Any]] = []
        cmd = f"{self._get_brew_cmd()} search {query}"
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
                        "description": "Homebrew formula",
                        "backend": self.alias,
                        "installed": False,
                    })
        return results

    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} update && {self._get_brew_cmd()} upgrade"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def sync(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} update"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def list_installed(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not self.is_available():
            return results

        cmd = f"{self._get_brew_cmd()} list --formula --versions"
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
                        "description": "Homebrew installed formula",
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

        cmd = f"{self._get_brew_cmd()} info --json=v2 {package}"
        ret, out = run_command(cmd, sudo=False, print_output=False)
        if ret == 0:
            import json
            try:
                parsed = json.loads(out)
                formulae = parsed.get("formulae", [])
                if formulae:
                    f = formulae[0]
                    info_data["version"] = f.get("versions", {}).get("stable", "unknown")
                    info_data["description"] = f.get("desc", "")
                    info_data["homepage"] = f.get("homepage", "")
                    info_data["installed"] = bool(f.get("installed", []))
            except Exception:
                pass
        info_data["raw"] = out
        return info_data

    def clean(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"{self._get_brew_cmd()} cleanup"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0
