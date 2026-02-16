from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from modules import ui_helpers


class TitleBar(QFrame):
    def __init__(self):
        super().__init__()
        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()
        self.setParent(None)

        self.setObjectName("title_bar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Stickerß")
        self.label.setStyleSheet(f"color: #999; font-size: {10 * self.scaleFactor}px")
        self.layout.addWidget(self.label)

        self.spacer = QSpacerItem(int(400 * self.scaleFactor), 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(self.spacer)

        self.setStyleSheet("""
            #title_bar {
                border-bottom: 1px solid #333;
                background: transparent;
                padding: 0 0 0 0;
            }
            QPushButton {
                border-radius: 5px;
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)

        icon_px = int(round(20 * self.scaleFactor))
        btn_px = int(round(20 * self.scaleFactor))

        button_color = QColor("#E6E6E6")

        self.close_button = QPushButton("")
        self.close_button.setFixedSize(btn_px, btn_px)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setIcon(ui_helpers.svg_to_icon("utils/ui/x.svg", QSize(icon_px, icon_px), button_color))
        self.close_button.setIconSize(QSize(icon_px, icon_px))

        self.settings_button = QPushButton("")
        self.settings_button.setFixedSize(btn_px, btn_px)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setIcon(ui_helpers.svg_to_icon("utils/ui/settings.svg", QSize(icon_px, icon_px), button_color))
        self.settings_button.setIconSize(QSize(int(icon_px - (5 * self.scaleFactor)), int(icon_px - (5 * self.scaleFactor))))

        self.layout.addWidget(self.settings_button)
        self.layout.addWidget(self.close_button)
