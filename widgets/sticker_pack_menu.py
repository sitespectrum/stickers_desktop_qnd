from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu

class PackMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)

        self.redownload = self.addAction("Redownload")
        self.download = self.addAction("Download")
        self.addSeparator()
        self.delete_action = self.addAction("Delete")
        self.remove_action = self.addAction("Remove from profile")

        self.setStyleSheet("""
            QMenu {
                background-color: #111;
                border-radius: 6px;
                padding: 0;
                margin: 0;
            }

            QMenu::item {
                color: #ccc;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background-color: #333;
            }

            QMenu::item:pressed {
                background-color: #444;
            }

            QMenu::separator {
                height: 1px;
                background: #222;
                margin: 4px 0;
            }
        """)
