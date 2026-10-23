"""Portage Binary Packages (:ebins) backend implementation."""
from typing import Any, Callable, Dict, List, Optional
from neo.backends.ebuild import EbuildBackend
from neo.utils import check_command_exists, run_command

try:
    import neo_core
except ImportError:
    neo_core = None

class EbinsBackend(EbuildBackend):
    name = "Portage Binary"
    alias = "ebins"

    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f"emerge --ask=n --getbinpkg {package}"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = "emerge --update --deep --newuse --getbinpkg @world"
        ret, _ = run_command(cmd, sudo=True, line_callback=line_callback)
        return ret == 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        results = super().search(query)
        for r in results:
            r["backend"] = self.alias
            r["is_binary"] = True
        return results

    def list_installed(self) -> List[Dict[str, Any]]:
        results = super().list_installed()
        for r in results:
            r["backend"] = self.alias
            r["description"] = "Portage package (binary capable)"
        return results

    def info(self, package: str) -> Dict[str, Any]:
        info_data = super().info(package)
        info_data["backend"] = self.alias
        info_data["binary_mode"] = True
        ret, out = run_command(f"emerge -pv --getbinpkg {package}", sudo=False, print_output=False)
        info_data["raw"] = out
        return info_data

    def clean(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        if check_command_exists("eclean-pkg"):
            ret, _ = run_command("eclean-pkg", sudo=True, line_callback=line_callback)
            return ret == 0
        return super().clean(line_callback=line_callback)
