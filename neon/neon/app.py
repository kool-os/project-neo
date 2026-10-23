"""Application entry point for neon GUI."""
import sys
import traceback
from PyQt6.QtCore import Qt, qInstallMessageHandler, QtMsgType
from PyQt6.QtWidgets import QApplication, QMessageBox
from neon.main_window import MainWindow
from neon.theme import apply_theme


def qt_message_handler(msg_type, context, message):
    """Suppress non-critical Qt internal messages."""
    if msg_type == QtMsgType.QtWarningMsg and "Palette" in message:
        return  # suppress palette warnings
    levels = {
        QtMsgType.QtDebugMsg: "DEBUG",
        QtMsgType.QtInfoMsg: "INFO",
        QtMsgType.QtWarningMsg: "WARNING",
        QtMsgType.QtCriticalMsg: "CRITICAL",
        QtMsgType.QtFatalMsg: "FATAL",
    }
    print(f"[Qt {levels.get(msg_type, '?')}] {message}", file=sys.stderr)


def handle_exception(exc_type, exc_value, exc_tb):
    """Global Python exception handler — show dialog instead of silent crash."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    error_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[neon] Unhandled exception:\n{error_text}", file=sys.stderr)
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("neon — Unhandled Error")
        msg.setText(f"<b>{exc_type.__name__}</b>: {exc_value}")
        msg.setDetailedText(error_text)
        msg.exec()
    except Exception:
        pass


def main():
    """Main function launching the neon PyQt6 GUI."""
    # Install handlers before creating QApplication
    sys.excepthook = handle_exception
    qInstallMessageHandler(qt_message_handler)

    app = QApplication(sys.argv)
    app.setApplicationName("neon")
    app.setApplicationDisplayName("neon - Unified Package Manager")

    # Apply modern dark theme
    apply_theme(app)

    # Initialize and show main window
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
