from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton


class PackNotDownloaded(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pack_not_downloaded")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setFixedSize(int(250 * self.scaleFactor), int(70 * self.scaleFactor))
        self.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
            #pack_not_downloaded {
                background-color: #121212; 
                border-radius: 5px; 
                border: 1px solid #ccc; 
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

        self.title = QLabel("This pack is not downloaded.")
        self.title.setStyleSheet(f"font-weight: bold; font-size: {11 * self.scaleFactor}px;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description = QLabel("Click the button below to download and use this pack.")
        self.description.setStyleSheet(f"font-size: {9 * self.scaleFactor}px;")
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.download_button = QPushButton("Download")
        self.button_layout = QVBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.download_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.button_layout.addWidget(self.download_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.description)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setVisible(False)
