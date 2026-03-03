from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QLabel, QHBoxLayout, QWidget


class ConfirmDeleteBookmark(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("confirm_delete_bookmark")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setFixedSize(int(300 * self.scaleFactor), int(80 * self.scaleFactor))

        self.setStyleSheet(f"""
        #confirm_delete_bookmark {{
            background-color: #121212; 
            border-radius: 5px; 
            border: 1px solid #ccc; 
        }}
        QPushButton {{
            background-color: #222;
            border-radius: 5px;
            padding: {int(5 * self.scaleFactor)}px;
        }}
        QPushButton:disabled {{
            background-color: #444;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: #333;
        }}
        QPushButton:pressed {{
            background-color: #444;
        }}
        #title {{
            font-size: {int(12 * self.scaleFactor)}px;
            text-align: center;
        }}
        """)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("<b>Delete Bookmark?</b>")
        self.title_label.setObjectName("title")
        self.main_layout.addWidget(self.title_label)

        self.description_label = QLabel("This action cannot be undone.")
        self.description_label.setObjectName("description")
        self.main_layout.addWidget(self.description_label)

        self.main_layout.addStretch()

        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(int(140 * self.scaleFactor), int(20 * self.scaleFactor))
        self.button_layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.hide)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.confirm_button = QPushButton("Delete")
        self.confirm_button.setFixedSize(int(140 * self.scaleFactor), int(20 * self.scaleFactor))
        self.button_layout.addWidget(self.confirm_button)
        self.confirm_button.clicked.connect(self.hide)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.hide()