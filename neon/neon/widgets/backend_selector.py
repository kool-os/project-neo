"""Sidebar backend selector widget."""
from typing import Dict
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from neon.theme import BACKEND_COLORS

BACKENDS = [
    ("all", "All Backends", "🌐"),
    ("ebuild", "ebuild (Portage)", "📦"),
    ("flatp", "flatp (Flatpak)", "📦"),
    ("brew", "brew (Homebrew)", "🍺"),
    ("cask", "cask (Cask)", "🍷"),
    ("ebins", "ebins (Binpkgs)", "⚡"),
]

class BackendButton(QPushButton):
    def __init__(self, alias: str, label: str, icon_str: str, parent=None):
        super().__init__(parent)
        self.alias = alias
        self.label_text = label
        self.icon_str = icon_str
        self.count = 0
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_text()

    def set_count(self, count: int):
        self.count = count
        self._update_text()

    def _update_text(self):
        color = BACKEND_COLORS.get(self.alias, "#cdd6f4")
        if self.count > 0:
            count_str = f" ({self.count})"
        else:
            count_str = ""
        self.setText(f"{self.icon_str}  {self.label_text}{count_str}")
        
        # Style button with accent indicator on check
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 12px;
                border-radius: 6px;
                border: 1px solid #313244;
                background-color: #181825;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #313244;
                border-color: {color};
            }}
            QPushButton:checked {{
                background-color: #2b2b3d;
                border-left: 4px solid {color};
                font-weight: bold;
                color: #ffffff;
            }}
        """)

class BackendSelectorWidget(QFrame):
    """Left sidebar widget allowing user to filter/select backends."""
    backend_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)
        self.setStyleSheet("background-color: #11111b; border-right: 1px solid #313244;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        # Title
        title_label = QLabel("BACKENDS")
        title_label.setStyleSheet("color: #6c7086; font-size: 11px; font-weight: bold; padding-left: 4px;")
        layout.addWidget(title_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons: Dict[str, BackendButton] = {}

        for alias, name, icon in BACKENDS:
            btn = BackendButton(alias, name, icon)
            if alias == "all":
                btn.setChecked(True)
            self.button_group.addButton(btn)
            self.buttons[alias] = btn
            layout.addWidget(btn)

            btn.clicked.connect(lambda checked, a=alias: self.backend_selected.emit(a))

        layout.addStretch()

        # Status note
        gentoo_badge = QLabel("Gentoo Linux")
        gentoo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gentoo_badge.setStyleSheet("color: #a6adc8; background-color: #1e1e2e; border-radius: 4px; padding: 6px; font-size: 11px;")
        layout.addWidget(gentoo_badge)

    def update_count(self, backend: str, count: int):
        if backend in self.buttons:
            self.buttons[backend].set_count(count)
        # Update 'all' total
        total = sum(b.count for alias, b in self.buttons.items() if alias != "all")
        if "all" in self.buttons:
            self.buttons["all"].set_count(total)

    def select_backend(self, backend: str):
        if backend in self.buttons:
            self.buttons[backend].setChecked(True)
            self.backend_selected.emit(backend)
