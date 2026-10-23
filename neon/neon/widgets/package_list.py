"""Table widget for displaying package lists."""
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)
from neon.theme import BACKEND_COLORS

class PackageListWidget(QTableWidget):
    """Table showing packages with Name, Version, Description, Status, Backend."""
    package_selected = pyqtSignal(dict)
    package_double_clicked = pyqtSignal(dict)

    COLUMNS = ["Name", "Version", "Description", "Status", "Backend"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packages_data: List[Dict[str, Any]] = []

        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_double_clicked)

    def set_packages(self, packages: List[Dict[str, Any]]):
        self.packages_data = packages
        self.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            desc = pkg.get("description", "")
            installed = pkg.get("installed", False)
            backend = pkg.get("backend", "")

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pkg)
            name_item.setForeground(QColor("#cdd6f4"))
            self.setItem(row, 0, name_item)

            # Version
            ver_item = QTableWidgetItem(version)
            ver_item.setForeground(QColor("#f9e2af"))
            self.setItem(row, 1, ver_item)

            # Description
            desc_item = QTableWidgetItem(desc)
            desc_item.setForeground(QColor("#a6adc8"))
            self.setItem(row, 2, desc_item)

            # Status
            status_text = "Installed ✓" if installed else "Available"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if installed:
                status_item.setForeground(QColor("#a6e3a1"))
            else:
                status_item.setForeground(QColor("#89dceb"))
            self.setItem(row, 3, status_item)

            # Backend
            b_item = QTableWidgetItem(f":{backend}")
            b_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            b_color = BACKEND_COLORS.get(backend, "#cdd6f4")
            b_item.setForeground(QColor(b_color))
            self.setItem(row, 4, b_item)

    def get_selected_package(self) -> Optional[Dict[str, Any]]:
        row = self.currentRow()
        if 0 <= row < len(self.packages_data):
            return self.packages_data[row]
        return None

    def _on_selection_changed(self):
        pkg = self.get_selected_package()
        if pkg:
            self.package_selected.emit(pkg)

    def _on_double_clicked(self, item: QTableWidgetItem):
        pkg = self.get_selected_package()
        if pkg:
            self.package_double_clicked.emit(pkg)

    def clear_packages(self):
        self.packages_data = []
        self.setRowCount(0)
