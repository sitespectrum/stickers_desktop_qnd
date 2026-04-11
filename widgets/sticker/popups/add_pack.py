from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton, QLineEdit, QWidget

from globals.user import user
from modules import ui_helpers
from widgets.sticker import sidebar, body


class AddPack(QFrame):
    def __init__(self, parent=None, body_widget: body.Body = None):
        super().__init__(parent)
        self.server_running = False
        self.setObjectName("add_pack")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.body_widget = body_widget
        self.sidebar_widget: sidebar.Sidebar | None = None

        self.current_user = user
        self.current_user.logged_inChanged.connect(self.update_buttons)

        self.scaleFactor = ui_helpers.get_screen_scale()

        self.setFixedSize(int(400 * self.scaleFactor), int(300 * self.scaleFactor))
        self.setStyleSheet("""
                    QWidget {
                        color: #ccc;
                    }
                    #add_pack {
                        background-color: #212121;
                    }
                    #close_button {
                        border-radius: 5px;
                        border: none;
                        background-color: transparent;
                    }
                    #close_button:hover {
                        background-color: #333;
                    }
                    #close_button:pressed {
                        background-color: #444;
                    }
                    QPushButton {
                        background-color: #111;
                        border-radius: 5px;
                    }
                    QPushButton:disabled {
                        background-color: #444;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #333;
                    }
                    QPushButton:pressed {
                        background-color: #444;
                    }
                """)

        self.setVisible(False)
        self.settings_open = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon_px = int(round(20 * self.scaleFactor))
        btn_px = int(round(20 * self.scaleFactor))

        button_color = QColor("#E6E6E6")

        self.close_button = QPushButton("")
        self.close_button.setObjectName("close_button")
        self.close_button.clicked.connect(self.close_popup)
        self.close_button.setFixedSize(btn_px, btn_px)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setIcon(ui_helpers.svg_to_icon("utils/ui/x.svg", QSize(icon_px, icon_px), button_color))
        self.close_button.setIconSize(QSize(icon_px, icon_px))

        self.title = QLabel("Add pack")
        self.title.setStyleSheet(f"font-size: {14 * self.scaleFactor}px; font-weight: bold;")

        self.pack_name_label = QLabel("Pack name")
        self.pack_name_label.setStyleSheet(f"font-size: {12 * self.scaleFactor}px;")

        self.pack_input = QLineEdit()
        self.pack_input.setPlaceholderText("Enter pack name")
        self.pack_input.setFixedHeight(int(20 * self.scaleFactor))
        self.pack_input.setFixedWidth(int(200 * self.scaleFactor))

        self.add_button = QPushButton("Add to profile")
        self.add_button.setFixedSize(int(200 * self.scaleFactor), int(20 * self.scaleFactor))
        self.add_button.clicked.connect(self.add_pack)

        self.download_and_add_button = QPushButton("Download and add to profile")
        self.download_and_add_button.setFixedSize(int(200 * self.scaleFactor), int(20 * self.scaleFactor))
        self.download_and_add_button.clicked.connect(self.add_and_download_pack)

        self.download_button = QPushButton("Download")
        self.download_button.setFixedSize(int(200 * self.scaleFactor), int(20 * self.scaleFactor))
        self.download_button.clicked.connect(self.download_pack)

        self.download_already_running_label = QLabel("Another download is already in progress")
        self.download_already_running_label.setStyleSheet(f"font-size: {10 * self.scaleFactor}px; color: #ff5555;")
        self.download_already_running_label.setHidden(True)

        self.layout.addWidget(self.close_button)
        self.layout.addWidget(self.title)
        self.layout.addSpacing(int(10 * self.scaleFactor))
        self.layout.addWidget(self.pack_name_label)
        self.layout.addWidget(self.pack_input)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.download_and_add_button)
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.download_already_running_label)

    def begin_loading(self):
        self.add_button.setDisabled(True)
        self.download_and_add_button.setDisabled(True)
        self.download_button.setDisabled(True)

        self.add_button.setText("Loading...")
        self.download_and_add_button.setText("Loading...")
        self.download_button.setText("Loading...")

    def end_loading(self):
        self.add_button.setDisabled(False)
        self.download_and_add_button.setDisabled(False)
        self.download_button.setDisabled(False)

        self.add_button.setText("Add to profile")
        self.download_and_add_button.setText("Download and add to profile")
        self.download_button.setText("Download")

    def update_buttons(self, logged_in: bool):
        if logged_in:
            self.add_button.setVisible(True)
            self.download_and_add_button.setVisible(True)
            self.download_button.setVisible(False)
        else:
            self.add_button.setVisible(False)
            self.download_and_add_button.setVisible(False)
            self.download_button.setVisible(True)

    def download_pack(self):
        self.download_already_running_label.setHidden(True)
        pack = self.pack_input.text()
        if not pack:
            return
        if self.body_widget.downloader.downloading:
            self.download_already_running_label.setHidden(False)
            return
        self.close_popup()
        self.body_widget.download_pack(pack, add=True, refresh_sidebar=True, close_popup=self.close_popup)

    def add_and_download_pack(self):
        self.download_already_running_label.setHidden(True)
        if not self.pack_input.text():
            return
        if self.body_widget.downloader.downloading:
            self.download_already_running_label.setHidden(False)
            return
        pack = self.pack_input.text()
        self.sidebar_widget.add_pack(pack)
        self.close_popup()
        self.body_widget.download_pack(pack, add=True, close_popup=self.close_popup)

    def add_pack(self):
        if not self.pack_input.text():
            return
        if not self.sidebar_widget:
            return
        self.sidebar_widget.add_pack(self.pack_input.text())

    def close_popup(self):
        self.setVisible(False)

    def open_popup(self):
        self.download_already_running_label.setHidden(True)
        self.setVisible(True)
        self.pack_input.setFocus()
        self.pack_input.clear()
