"""Flatpak (:flatp) backend implementation."""
import re
from typing import Any, Callable, Dict, List, Optional
from neo.backends.base import Backend
from neo.utils import check_command_exists, run_command

try:
    import neo_core
except ImportError:
    neo_core = None

class FlatpakBackend(Backend):
    name = "Flatpak"
    alias = "flatp"

    def is_available(self) -> bool:
        return check_command_exists("flatpak")

    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"flatpak install -y {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def remove(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"flatpak uninstall -y {package}"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        if neo_core is not None:
            try:
                res = neo_core.search_package(query, "flatp")
                if res:
                    return res
            except Exception:
                pass

        results: List[Dict[str, Any]] = []
        ret, out = run_command(
            f"flatpak search {query} --columns=name,application,version,description",
            sudo=False,
            print_output=False,
        )
        if ret == 0:
            lines = out.splitlines()
            for line in lines[1:]:  # skip header
                parts = line.split("\t")
                if len(parts) >= 4:
                    app_id = parts[1].strip()
                    app_name = parts[0].strip()
                    results.append({
                        "name": app_id if app_id else app_name,
                        "display_name": app_name,
                        "version": parts[2].strip() or "latest",
                        "description": parts[3].strip(),
                        "backend": self.alias,
                        "installed": False,
                    })
        return results

    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "flatpak update -y"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def sync(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "flatpak update --appstream -y"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0

    def list_installed(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not self.is_available():
            return results

        ret, out = run_command("flatpak list --app --columns=name,application,version,description", sudo=False, print_output=False)
        if ret == 0:
            for line in out.splitlines()[1:]:
                parts = line.split("\t")
                if len(parts) >= 2:
                    app_name = parts[0].strip()
                    app_id = parts[1].strip()
                    version = parts[2].strip() if len(parts) > 2 else "installed"
                    desc = parts[3].strip() if len(parts) > 3 else "Flatpak application"
                    results.append({
                        "name": app_id if app_id else app_name,
                        "display_name": app_name,
                        "version": version or "installed",
                        "description": desc,
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
            "installed": False,
        }
        if not self.is_available():
            return info_data

        ret, out = run_command(f"flatpak info {package}", sudo=False, print_output=False)
        if ret == 0:
            info_data["installed"] = True
            for line in out.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == "version":
                        info_data["version"] = val
                    elif key == "summary":
                        info_data["description"] = val
        info_data["raw"] = out
        return info_data

    def clean(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "flatpak uninstall --unused -y"
        ret, _ = run_command(cmd, sudo=False, line_callback=line_callback)
        return ret == 0
