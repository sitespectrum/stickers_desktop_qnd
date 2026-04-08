import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton

from modules import ui_helpers
from modules.ui_helpers import svg_to_icon


class Menu(QFrame):
    def __init__(self, stacked_widget_trigger=None, parent=None):
        super().__init__(parent)
        self.setObjectName("menu")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.scaleFactor = ui_helpers.get_screen_scale()

        self.stacked_widget_trigger = stacked_widget_trigger

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(int(5 * self.scaleFactor), int(5 * self.scaleFactor), int(5 * self.scaleFactor),
                                       int(5 * self.scaleFactor))

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

        icon_px = int(round(20 * self.scaleFactor))
        btn_px = int(round(20 * self.scaleFactor))

        button_color = QColor("#E6E6E6")

        self.stickers_button = QPushButton("Stickers")
        self.stickers_button.setFixedSize(int(100 * self.scaleFactor), btn_px)
        self.stickers_button.clicked.connect(
            lambda checked=False, triggered="stickers": self.stacked_widget_trigger(triggered))
        self.stickers_button.setIcon(
            svg_to_icon(os.path.join("utils", "ui", "sticker.svg"), QSize(icon_px, icon_px), button_color))
        self.layout.addWidget(self.stickers_button)

        self.notes_button = QPushButton("Notes")
        self.notes_button.setFixedSize(int(100 * self.scaleFactor), btn_px)
        self.notes_button.clicked.connect(
            lambda checked=False, triggered="notes": self.stacked_widget_trigger(triggered))
        self.notes_button.setIcon(
            svg_to_icon(os.path.join("utils", "ui", "notebook.svg"), QSize(icon_px, icon_px), button_color))
        self.layout.addWidget(self.notes_button)

        self.bookmarks_button = QPushButton("Bookmarks")
        self.bookmarks_button.setFixedSize(int(100 * self.scaleFactor), btn_px)
        self.bookmarks_button.clicked.connect(
            lambda checked=False, triggered="bookmarks": self.stacked_widget_trigger(triggered))
        self.bookmarks_button.setIcon(
            svg_to_icon(os.path.join("utils", "ui", "bookmark.svg"), QSize(icon_px, icon_px), button_color))
        self.layout.addWidget(self.bookmarks_button)

        self.setFixedSize(self.layout.sizeHint())
