import ctypes

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton


class PackNotDownloaded(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pack_not_downloaded")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

        self.setFixedSize(250 * self.scaleFactor, 70 * self.scaleFactor)
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

        self.title = QLabel("This pack is not downloaded yet.")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description = QLabel("Click on the button below to download it.")
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.download_button = QPushButton("Download")
        self.button_layout = QVBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.download_button.setFixedSize(100 * self.scaleFactor, 20 * self.scaleFactor)
        self.button_layout.addWidget(self.download_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.description)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setVisible(False)
