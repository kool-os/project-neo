"""Main application window for neon GUI."""
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from neo.backends import (
    get_all_backends,
    get_available_backends,
    get_backend,
    resolve_backend,
)
from neon.widgets.backend_selector import BackendSelectorWidget
from neon.widgets.package_list import PackageListWidget
from neon.widgets.search_bar import SearchBarWidget
from neon.widgets.terminal_output import TerminalOutputWidget

class OperationWorker(QThread):
    """Worker thread to run backend package operations without blocking the UI."""
    output_line = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation_type: str, backend_alias: str, package: Optional[str] = None):
        super().__init__()
        self.operation_type = operation_type
        self.backend_alias = backend_alias
        self.package = package

    def run(self):
        backend = get_backend(self.backend_alias)
        if not backend:
            self.output_line.emit(f"Error: Unknown backend '{self.backend_alias}'\n")
            self.finished.emit(False, "Unknown backend")
            return

        def line_cb(line: str):
            self.output_line.emit(line)

        success = False
        msg = ""

        try:
            if self.operation_type == "install" and self.package:
                self.output_line.emit(f"==> Installing {self.package} via :{backend.alias}...\n")
                success = backend.install(self.package, line_callback=line_cb)
                msg = f"Installation of {self.package} {'succeeded' if success else 'failed'}"

            elif self.operation_type == "remove" and self.package:
                self.output_line.emit(f"==> Removing {self.package} via :{backend.alias}...\n")
                success = backend.remove(self.package, line_callback=line_cb)
                msg = f"Removal of {self.package} {'succeeded' if success else 'failed'}"

            elif self.operation_type == "update":
                self.output_line.emit(f"==> Updating packages via :{backend.alias}...\n")
                success = backend.update(line_callback=line_cb)
                msg = f"Update on :{backend.alias} {'succeeded' if success else 'failed'}"

            elif self.operation_type == "sync":
                self.output_line.emit(f"==> Syncing database for :{backend.alias}...\n")
                success = backend.sync(line_callback=line_cb)
                msg = f"Database sync on :{backend.alias} {'succeeded' if success else 'failed'}"

            elif self.operation_type == "clean":
                self.output_line.emit(f"==> Cleaning cache for :{backend.alias}...\n")
                success = backend.clean(line_callback=line_cb)
                msg = f"Cache clean on :{backend.alias} {'succeeded' if success else 'failed'}"

        except Exception as e:
            self.output_line.emit(f"\nExecution error: {e}\n")
            success = False
            msg = str(e)

        self.finished.emit(success, msg)

class FetchPackagesWorker(QThread):
    """Worker thread to fetch installed packages or search results in the background."""
    packages_ready = pyqtSignal(list)
    count_ready = pyqtSignal(str, int)

    def __init__(self, mode: str, backend_filter: str = "all", query: str = ""):
        super().__init__()
        self.mode = mode  # "installed", "search", "count_all"
        self.backend_filter = backend_filter
        self.query = query

    def run(self):
        if self.mode == "count_all":
            avail = get_available_backends()
            for alias, b in avail.items():
                try:
                    pkgs = b.list_installed()
                    self.count_ready.emit(alias, len(pkgs))
                except Exception:
                    self.count_ready.emit(alias, 0)
            return

        if self.mode == "installed":
            results = []
            if self.backend_filter == "all":
                avail = get_available_backends()
                for alias, b in avail.items():
                    try:
                        results.extend(b.list_installed())
                    except Exception:
                        pass
            else:
                b = get_backend(self.backend_filter)
                if b and b.is_available():
                    results = b.list_installed()
            self.packages_ready.emit(results)

        elif self.mode == "search":
            results = []
            if self.backend_filter == "all":
                # Check neo_core parallel search
                try:
                    import neo_core
                    avail = get_available_backends()
                    backends_list = list(avail.keys())
                    core_res = neo_core.parallel_search([self.query], backends_list)
                    if isinstance(core_res, dict):
                        for b_key, items in core_res.items():
                            if isinstance(items, list):
                                results.extend(items)
                except Exception:
                    avail = get_available_backends()
                    for alias, b in avail.items():
                        try:
                            results.extend(b.search(self.query))
                        except Exception:
                            pass
            else:
                b = get_backend(self.backend_filter)
                if b:
                    results = b.search(self.query)
            self.packages_ready.emit(results)

class MainWindow(QMainWindow):
    """Main application window for neon GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("neon - Unified Package Manager (Gentoo)")
        self.resize(1100, 750)

        self.current_backend_filter = "all"
        self.active_worker: Optional[QThread] = None

        self._init_ui()
        self._load_installed_counts()
        self._load_packages()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Left Sidebar (Backend Selector)
        self.sidebar = BackendSelectorWidget(self)
        self.sidebar.backend_selected.connect(self._on_sidebar_backend_selected)
        root_layout.addWidget(self.sidebar)

        # Right Content Area
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # Top Bar: Search Bar + Action Buttons
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(8)

        self.search_bar = SearchBarWidget(self)
        self.search_bar.search_requested.connect(self._on_search_requested)
        top_bar_layout.addWidget(self.search_bar, stretch=1)

        # Action Buttons
        self.btn_install = QPushButton("📥 Install")
        self.btn_install.setObjectName("actionInstall")
        self.btn_install.clicked.connect(self._on_install_clicked)
        top_bar_layout.addWidget(self.btn_install)

        self.btn_remove = QPushButton("🗑️ Remove")
        self.btn_remove.setObjectName("actionRemove")
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        top_bar_layout.addWidget(self.btn_remove)

        self.btn_update = QPushButton("🔄 Update")
        self.btn_update.setObjectName("actionUpdate")
        self.btn_update.clicked.connect(self._on_update_clicked)
        top_bar_layout.addWidget(self.btn_update)

        self.btn_sync = QPushButton("🔃 Sync")
        self.btn_sync.clicked.connect(self._on_sync_clicked)
        top_bar_layout.addWidget(self.btn_sync)

        self.btn_clean = QPushButton("🧹 Clean")
        self.btn_clean.clicked.connect(self._on_clean_clicked)
        top_bar_layout.addWidget(self.btn_clean)

        content_layout.addLayout(top_bar_layout)

        # Main Vertical Splitter: Package Table + Terminal Output
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # Package Table
        self.package_table = PackageListWidget(self)
        self.package_table.package_selected.connect(self._on_package_selected)
        self.package_table.package_double_clicked.connect(self._on_package_double_clicked)
        self.splitter.addWidget(self.package_table)

        # Bottom Panel: Terminal Output
        self.terminal_output = TerminalOutputWidget(self)
        self.splitter.addWidget(self.terminal_output)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        content_layout.addWidget(self.splitter, stretch=1)
        root_layout.addWidget(content_widget, stretch=1)

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. All backends operational.")

    def _load_installed_counts(self):
        self.count_worker = FetchPackagesWorker(mode="count_all")
        self.count_worker.count_ready.connect(self.sidebar.update_count)
        self.count_worker.start()

    def _load_packages(self):
        self.status_bar.showMessage(f"Loading packages for :{self.current_backend_filter}...")
        self.fetch_worker = FetchPackagesWorker(mode="installed", backend_filter=self.current_backend_filter)
        self.fetch_worker.packages_ready.connect(self._on_packages_loaded)
        self.fetch_worker.start()

    def _on_packages_loaded(self, packages: List[Dict[str, Any]]):
        self.package_table.set_packages(packages)
        self.status_bar.showMessage(f"Showing {len(packages)} packages ({self.current_backend_filter}).")

    def _on_sidebar_backend_selected(self, backend: str):
        self.current_backend_filter = backend
        self.search_bar.set_backend(backend)
        query = self.search_bar.get_query()
        if query:
            self._on_search_requested(query, backend)
        else:
            self._load_packages()

    def _on_search_requested(self, query: str, backend_filter: str):
        if not query:
            self._load_packages()
            return

        self.status_bar.showMessage(f"Searching for '{query}'...")
        self.search_worker = FetchPackagesWorker(mode="search", backend_filter=backend_filter, query=query)
        self.search_worker.packages_ready.connect(self._on_packages_loaded)
        self.search_worker.start()

    def _on_package_selected(self, pkg: Dict[str, Any]):
        installed = pkg.get("installed", False)
        name = pkg.get("name", "")
        backend = pkg.get("backend", "")
        self.btn_install.setEnabled(not installed)
        self.btn_remove.setEnabled(installed)
        self.status_bar.showMessage(f"Selected: {name} [:{backend}] ({'Installed' if installed else 'Available'})")

    def _on_package_double_clicked(self, pkg: Dict[str, Any]):
        name = pkg.get("name", "")
        backend = pkg.get("backend", "")
        installed = pkg.get("installed", False)

        if installed:
            ans = QMessageBox.question(
                self,
                "Remove Package",
                f"Do you want to remove package '{name}' via :{backend}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans == QMessageBox.StandardButton.Yes:
                self._run_operation("remove", backend, name)
        else:
            ans = QMessageBox.question(
                self,
                "Install Package",
                f"Do you want to install package '{name}' via :{backend}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans == QMessageBox.StandardButton.Yes:
                self._run_operation("install", backend, name)

    def _on_install_clicked(self):
        pkg = self.package_table.get_selected_package()
        if pkg:
            name = pkg.get("name")
            backend = pkg.get("backend") or self._get_effective_backend()
            self._run_operation("install", backend, name)
        else:
            pkg_name, ok = QInputDialog.getText(self, "Install Package", "Enter package name (e.g. firefox, vim):")
            if ok and pkg_name.strip():
                backend = self._get_effective_backend()
                self._run_operation("install", backend, pkg_name.strip())

    def _on_remove_clicked(self):
        pkg = self.package_table.get_selected_package()
        if pkg:
            name = pkg.get("name")
            backend = pkg.get("backend") or self._get_effective_backend()
            self._run_operation("remove", backend, name)

    def _on_update_clicked(self):
        backend = self._get_effective_backend()
        self._run_operation("update", backend)

    def _on_sync_clicked(self):
        backend = self._get_effective_backend()
        self._run_operation("sync", backend)

    def _on_clean_clicked(self):
        backend = self._get_effective_backend()
        self._run_operation("clean", backend)

    def _get_effective_backend(self) -> str:
        if self.current_backend_filter != "all":
            return self.current_backend_filter
        return resolve_backend().alias

    def _run_operation(self, op_type: str, backend_alias: str, package: Optional[str] = None):
        self._set_ui_busy(True)
        self.terminal_output.append_text(f"\n--- Starting {op_type.upper()} operation ---\n")

        self.op_worker = OperationWorker(op_type, backend_alias, package)
        self.op_worker.output_line.connect(self.terminal_output.append_text)
        self.op_worker.finished.connect(self._on_operation_finished)
        self.op_worker.start()

    def _on_operation_finished(self, success: bool, message: str):
        self._set_ui_busy(False)
        self.status_bar.showMessage(message)
        self.terminal_output.append_text(f"\n--- Operation completed: {message} ---\n")
        self._load_installed_counts()
        self._load_packages()

    def _set_ui_busy(self, busy: bool):
        self.btn_install.setEnabled(not busy)
        self.btn_remove.setEnabled(not busy)
        self.btn_update.setEnabled(not busy)
        self.btn_sync.setEnabled(not busy)
        self.btn_clean.setEnabled(not busy)
        if busy:
            self.status_bar.showMessage("Operation in progress...")
