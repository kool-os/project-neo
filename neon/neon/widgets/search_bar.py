"""Search bar widget with backend filter dropdown."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

class SearchBarWidget(QWidget):
    """Search input with backend dropdown filter and search action."""
    search_requested = pyqtSignal(str, str)  # query, backend_filter

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages across backends (e.g. vim, firefox, gcc)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._emit_search)
        layout.addWidget(self.search_input, stretch=1)

        # Backend selector dropdown
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("All Backends", "all")
        self.backend_combo.addItem(":ebuild (Portage)", "ebuild")
        self.backend_combo.addItem(":flatp (Flatpak)", "flatp")
        self.backend_combo.addItem(":brew (Homebrew)", "brew")
        self.backend_combo.addItem(":cask (Homebrew Cask)", "cask")
        self.backend_combo.addItem(":ebins (Binary pkgs)", "ebins")
        layout.addWidget(self.backend_combo)

        # Search Button
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.clicked.connect(self._emit_search)
        layout.addWidget(self.search_btn)

    def _emit_search(self):
        query = self.search_input.text().strip()
        backend_filter = self.backend_combo.currentData()
        self.search_requested.emit(query, backend_filter)

    def set_backend(self, backend: str):
        idx = self.backend_combo.findData(backend)
        if idx >= 0:
            self.backend_combo.setCurrentIndex(idx)
        else:
            self.backend_combo.setCurrentIndex(0)

    def get_query(self) -> str:
        return self.search_input.text().strip()
