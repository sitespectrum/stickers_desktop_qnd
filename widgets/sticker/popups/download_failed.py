from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton

from modules import ui_helpers


class DownloadFailed(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("download_failed")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scaleFactor = ui_helpers.get_screen_scale()

        self.setFixedSize(int(250 * self.scaleFactor), int(70 * self.scaleFactor))
        self.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
            #download_failed {
                background-color: #121212; 
                border-radius: 5px; 
                border: 2px solid red; 
            }
            QPushButton {
                background-color: #333;
                border-radius: 5px;
                color: #ddd;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #555;
            }
        """)

        self.title = QLabel("Failed to download pack.")
        self.title.setStyleSheet(f"font-weight: bold; font-size: {11 * self.scaleFactor}px;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description = QLabel()
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_layout = QVBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_button = QPushButton("Close")
        self.close_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.close_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.close_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.description)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setVisible(False)
