"""Portage (:ebuild) backend implementation."""
import os
import re
import subprocess
from typing import Any, Callable, Dict, List, Optional
from neo.backends.base import Backend
from neo.utils import check_command_exists, run_command

try:
    import neo_core
except ImportError:
    neo_core = None

class EbuildBackend(Backend):
    name = "Portage Ebuild"
    alias = "ebuild"

    def is_available(self) -> bool:
        return check_command_exists("emerge")

    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"emerge --ask=n {package}"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def remove(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"emerge --depclean {package}"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        if neo_core is not None:
            try:
                res = neo_core.search_package(query, "ebuild")
                if res:
                    return res
            except Exception:
                pass

        results: List[Dict[str, Any]] = []
        if check_command_exists("eix"):
            ret, out = run_command(f"eix --compact -c {query}", sudo=False, print_output=False)
            for line in out.splitlines():
                line = line.strip()
                if line:
                    results.append({
                        "name": line,
                        "version": "available",
                        "description": "Portage package",
                        "backend": self.alias,
                        "installed": False,
                    })
            if results:
                return results

        # Fallback to emerge --search
        ret, out = run_command(f"emerge --search {query}", sudo=False, print_output=False)
        cur_pkg: Optional[Dict[str, Any]] = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("*"):
                if cur_pkg:
                    results.append(cur_pkg)
                pkg_name = line.replace("*", "").strip()
                cur_pkg = {
                    "name": pkg_name,
                    "version": "unknown",
                    "description": "",
                    "backend": self.alias,
                    "installed": False,
                }
            elif cur_pkg and line.startswith("Latest version available:"):
                cur_pkg["version"] = line.split(":", 1)[1].strip()
            elif cur_pkg and line.startswith("Description:"):
                cur_pkg["description"] = line.split(":", 1)[1].strip()
        if cur_pkg:
            results.append(cur_pkg)

        return results

    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "emerge --update --deep --newuse @world"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def sync(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "emerge --sync"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def list_installed(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        if check_command_exists("qlist"):
            ret, out = run_command("qlist -Iv", sudo=False, print_output=False)
            if ret == 0:
                for line in out.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Format: category/name-version e.g. app-editors/vim-9.1.0700
                    # Match name and version
                    m = re.match(r"^(.+)-(\d+.*)$", line)
                    if m:
                        pkg_name = m.group(1)
                        pkg_ver = m.group(2)
                    else:
                        pkg_name = line
                        pkg_ver = "installed"
                    results.append({
                        "name": pkg_name,
                        "version": pkg_ver,
                        "description": "Portage installed package",
                        "backend": self.alias,
                        "installed": True,
                    })
                return results

        # Fallback: scan /var/db/pkg
        pkg_db = "/var/db/pkg"
        if os.path.exists(pkg_db):
            for cat in os.listdir(pkg_db):
                cat_path = os.path.join(pkg_db, cat)
                if not os.path.isdir(cat_path):
                    continue
                for pkg in os.listdir(cat_path):
                    m = re.match(r"^(.+)-(\d+.*)$", pkg)
                    if m:
                        pkg_name = f"{cat}/{m.group(1)}"
                        pkg_ver = m.group(2)
                    else:
                        pkg_name = f"{cat}/{pkg}"
                        pkg_ver = "installed"
                    results.append({
                        "name": pkg_name,
                        "version": pkg_ver,
                        "description": "Portage installed package",
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

        # Check equery meta if installed
        if check_command_exists("equery"):
            ret, out = run_command(f"equery meta {package}", sudo=False, print_output=False)
            if ret == 0:
                for line in out.splitlines():
                    if line.strip().startswith("Homepage:"):
                        info_data["homepage"] = line.split(":", 1)[1].strip()
                    elif line.strip().startswith("Description:"):
                        info_data["description"] = line.split(":", 1)[1].strip()

        # Check emerge -pv
        ret, out = run_command(f"emerge -pv {package}", sudo=False, print_output=False)
        info_data["raw"] = out
        return info_data

    def clean(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        if check_command_exists("eclean-dist"):
            ret, _ = run_command("eclean-dist", sudo=True, line_callback=line_callback)
            return ret == 0
        return True
