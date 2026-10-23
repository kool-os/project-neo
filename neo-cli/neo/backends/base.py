"""Abstract base class for all neo package backends."""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

class Backend(ABC):
    """Abstract interface that each package backend must implement."""
    name: str
    alias: str

    @abstractmethod
    def install(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Install a package."""
        ...

    @abstractmethod
    def remove(self, package: str, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Remove/uninstall a package."""
        ...

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for packages matching query. Returns list of dicts."""
        ...

    @abstractmethod
    def update(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Update system or backend packages."""
        ...

    @abstractmethod
    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed packages managed by this backend."""
        ...

    @abstractmethod
    def info(self, package: str) -> Dict[str, Any]:
        """Get detailed information about a package."""
        ...

    @abstractmethod
    def sync(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Synchronize package repository databases."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend's tools are available on the system."""
        ...

    def clean(self, line_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Clean backend caches. Default no-op if unsupported."""
        return True
