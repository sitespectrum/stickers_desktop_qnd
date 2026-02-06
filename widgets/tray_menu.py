from PySide6.QtWidgets import QMenu


class TrayMenu(QMenu):
    def __init__(self):
        super().__init__()

        self.quit_action = self.addAction("Quit")

        self.setStyleSheet("""
            QMenu {
                background-color: #111;
                border-radius: 0;
            }
            QMenu::item:selected {
                background-color: #333;
            }
            QMenu::item:pressed {
                background-color: #444;
            }
            QMenu::item {
                color: #999
            }
        """)
