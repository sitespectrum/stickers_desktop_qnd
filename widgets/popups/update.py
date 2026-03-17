from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

from globals.constants import VERSION
from modules import ui_helpers
from widgets import toast


class Update(QFrame):
    def __init__(self,toast_provider: toast.QToastProvider , parent=None):
        super().__init__(parent)
        self.setObjectName("update")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.latest_version = None

        self.toast_provider = toast_provider

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.top_bar = QHBoxLayout()
        self.top_bar.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addLayout(self.top_bar)

        icon_px = int(round(20 * self.scaleFactor))
        btn_px = int(round(20 * self.scaleFactor))

        button_color = QColor("#E6E6E6")

        self.close_button = QPushButton("")
        self.close_button.setObjectName("close_button")
        self.close_button.setFixedSize(btn_px, btn_px)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setIcon(ui_helpers.svg_to_icon("utils/ui/x.svg", QSize(icon_px, icon_px), button_color))
        self.close_button.setIconSize(QSize(icon_px, icon_px))

        self.top_bar.addWidget(self.close_button)

        self.title = QLabel("Update")
        self.title.setStyleSheet(f"font-size: {20 * self.scaleFactor}px; font-weight: bold;")
        self.layout.addWidget(self.title)

        self.current_version_label = QLabel(f"Current version: v{VERSION}")
        self.current_version_label.setStyleSheet(f"font-size: {12 * self.scaleFactor}px;")
        self.layout.addWidget(self.current_version_label)

        self.latest_version_label = QLabel()
        self.latest_version_label.setStyleSheet(f"font-size: {12 * self.scaleFactor}px;")
        self.layout.addWidget(self.latest_version_label)

        self.check_for_update_button = QPushButton("Check for updates")
        self.check_for_update_button.clicked.connect(self.check_for_update)
        self.check_for_update_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.layout.addWidget(self.check_for_update_button)

        self.setStyleSheet("""
            #update {
                background-color: #222;
                border-top-left-radius: 10px;
            }
        """)

        self.hide()

    def check_for_update(self):
        self.latest_version = "1.0.0"
        self.latest_version_label.setText(f"Latest version: v{self.latest_version}")
        if self.latest_version and self.latest_version != VERSION:
            self.toast_provider.show_toast("An update is available.", timeout=6000, variant="info")

    def open(self):
        self.show()
        self.raise_()