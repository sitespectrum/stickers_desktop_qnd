from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLineEdit, QLabel, QHBoxLayout, QWidget


class EditBookmark(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("edit_bookmark")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.bookmark_id = None

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setFixedSize(int(300 * self.scaleFactor), int(100 * self.scaleFactor))

        self.setStyleSheet(f"""
        #edit_bookmark, #overlay {{
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
        QScrollBar:vertical {{
            width: 3px;
            background: transparent;
        }}

        QScrollBar::handle:vertical {{
            background: #333;
            border-radius: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: #444;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: #000;
            border-radius: 2px;
        }}
        QScrollArea QWidget {{
            background-color: transparent;
        }}
        """)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("<b>Title:</b>")
        self.main_layout.addWidget(self.title_label)

        self.title = QLineEdit()
        self.main_layout.addWidget(self.title)

        self.content_label = QLabel("<b>URL:</b>")
        self.main_layout.addWidget(self.content_label)

        self.url = QLineEdit()
        self.main_layout.addWidget(self.url)

        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)

        self.delete_button = QPushButton("Delete")
        self.button_layout.addWidget(self.delete_button)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.button_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.button_layout.addWidget(self.close_button)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.save_button = QPushButton("Save")
        self.button_layout.addWidget(self.save_button)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.hide()

        self.overlay = QWidget()
        self.overlay_layout = QVBoxLayout()
        self.overlay.setLayout(self.overlay_layout)
        self.overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label = QLabel("Loading...")
        self.loading_label.setStyleSheet(f"font-size: {int(12 * self.scaleFactor)}px;")
        self.overlay_layout.addWidget(self.loading_label)
        self.overlay.setObjectName("overlay")
        self.overlay.setFixedSize(self.size())
        self.overlay.setParent(self)

    def loading(self):
        self.overlay.show()

    def end_loading(self):
        self.overlay.hide()

