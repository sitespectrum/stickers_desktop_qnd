from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy, QAbstractScrollArea


class Menu(QFrame):
    def __init__(self, stacked_widget_trigger=None, parent=None):
        super().__init__(parent)
        self.setObjectName("menu")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.stacked_widget_trigger = stacked_widget_trigger

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(int(5 * self.scaleFactor), int(5 * self.scaleFactor), int(5 * self.scaleFactor), int(5 * self.scaleFactor))

        self.setStyleSheet("""
        #menu {
            background-color: #212121;
            border-bottom-right-radius: 5px;
            border-right: 1px solid #333;
            border-bottom: 1px solid #333;
        }
        QPushButton {
            text-align: left;
            padding-left: 10px;
        }
        """)

        self.stickers_button = QPushButton("Stickers")
        self.stickers_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.stickers_button.clicked.connect(lambda checked=False, triggered="stickers":self.stacked_widget_trigger(triggered))
        self.layout.addWidget(self.stickers_button)

        self.notes_button = QPushButton("Notes")
        self.notes_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.notes_button.clicked.connect(lambda checked=False, triggered="notes":self.stacked_widget_trigger(triggered))
        self.layout.addWidget(self.notes_button)

        self.bookmarks_button = QPushButton("Bookmarks")
        self.bookmarks_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.bookmarks_button.clicked.connect(lambda checked=False, triggered="bookmarks":self.stacked_widget_trigger(triggered))
        self.layout.addWidget(self.bookmarks_button)

        self.setFixedSize(self.layout.sizeHint())
