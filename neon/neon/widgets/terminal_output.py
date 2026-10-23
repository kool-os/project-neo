"""Terminal output panel with real-time streaming and ANSI color rendering."""
import html
import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Standard ANSI 8-color map
ANSI_COLORS = {
    "30": "#585b70",  # Black / dark gray
    "31": "#f38ba8",  # Red
    "32": "#a6e3a1",  # Green
    "33": "#f9e2af",  # Yellow
    "34": "#89b4fa",  # Blue
    "35": "#f5c2e7",  # Magenta
    "36": "#94e2d5",  # Cyan
    "37": "#cdd6f4",  # White
    "90": "#6c7086",  # Bright Black
    "91": "#eba0ac",  # Bright Red
    "92": "#a6e3a1",  # Bright Green
    "93": "#f9e2af",  # Bright Yellow
    "94": "#89b4fa",  # Bright Blue
    "95": "#f5c2e7",  # Bright Magenta
    "96": "#94e2d5",  # Bright Cyan
    "97": "#ffffff",  # Bright White
}

def ansi_to_html(text: str) -> str:
    """Converts ANSI escape sequences into basic HTML colored spans."""
    escaped = html.escape(text)

    # Regex for ANSI escape codes \x1b[...m
    ansi_regex = re.compile(r"\x1b\[([0-9;]*)m")

    def replacer(match):
        codes = match.group(1).split(";")
        color = None
        bold = False

        for code in codes:
            if code == "0" or code == "":
                return "</span>"
            elif code == "1":
                bold = True
            elif code in ANSI_COLORS:
                color = ANSI_COLORS[code]

        styles = []
        if color:
            styles.append(f"color: {color};")
        if bold:
            styles.append("font-weight: bold;")

        if styles:
            return f"<span style=\"{' '.join(styles)}\">"
        return "<span>"

    result = ansi_regex.sub(replacer, escaped)
    result = result.replace("\n", "<br>")
    return result

class TerminalOutputWidget(QWidget):
    """Panel displaying real-time command terminal output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header toolbar
        hdr_layout = QHBoxLayout()
        hdr_layout.setContentsMargins(4, 2, 4, 2)
        
        self.title_label = QLabel("TERMINAL OUTPUT")
        self.title_label.setStyleSheet("color: #6c7086; font-size: 11px; font-weight: bold;")
        hdr_layout.addWidget(self.title_label)

        hdr_layout.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedHeight(24)
        self.clear_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.clear_btn.clicked.connect(self.clear_output)
        hdr_layout.addWidget(self.clear_btn)

        layout.addLayout(hdr_layout)

        # Text edit terminal view
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("terminalOutput")
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_edit)

    def append_text(self, text: str):
        """Append raw or ANSI-encoded text to the terminal view."""
        formatted_html = ansi_to_html(text)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(formatted_html)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def clear_output(self):
        self.text_edit.clear()
