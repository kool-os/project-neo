"""Dark theme styling and palette colors for neon."""

BACKEND_COLORS = {
    "ebuild": "#50fa7b",   # Gentoo / ebuild green
    "flatp": "#3584e4",    # Flatpak blue
    "brew": "#f1fa8c",     # Homebrew yellow
    "cask": "#ffb86c",     # Cask orange
    "ebins": "#00e676",    # Portage binary bright green
    "all": "#bd93f9",      # Purple for 'All'
}

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}

QMenuBar::item:selected {
    background-color: #313244;
}

QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
}

/* Sidebar / Buttons */
QToolBar {
    background-color: #181825;
    border: none;
    spacing: 6px;
    padding: 6px;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border-color: #313244;
}

/* Primary Action Buttons */
QPushButton#actionInstall {
    background-color: #2e7d32;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#actionInstall:hover {
    background-color: #388e3c;
}

QPushButton#actionRemove {
    background-color: #c62828;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#actionRemove:hover {
    background-color: #d32f2f;
}

QPushButton#actionUpdate {
    background-color: #0277bd;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#actionUpdate:hover {
    background-color: #0288d1;
}

/* Input Fields & Dropdowns */
QLineEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #585b70;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QComboBox {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 12px;
}

QComboBox:hover {
    border-color: #89b4fa;
}

QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #313244;
}

/* Package Table */
QTableWidget {
    background-color: #181825;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 6px;
    selection-background-color: #313244;
    selection-color: #cdd6f4;
}

QHeaderView::section {
    background-color: #11111b;
    color: #a6adc8;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #313244;
    padding: 6px;
}

/* Terminal Output */
QTextEdit#terminalOutput {
    background-color: #11111b;
    color: #a6e3a1;
    font-family: "DejaVu Sans Mono", "Fira Code", monospace;
    font-size: 12px;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #181825;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Splitter */
QSplitter::handle {
    background-color: #313244;
    height: 2px;
}
"""

def apply_theme(app):
    """Apply standard dark theme stylesheet to the Qt application."""
    app.setStyleSheet(DARK_STYLESHEET)
