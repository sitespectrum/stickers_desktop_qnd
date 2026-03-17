import json
import os.path
import shutil
import webbrowser
from zipfile import ZipFile

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QProgressBar

from globals.constants import VERSION, GITHUB_API
from modules import ui_helpers, request_helpers
from widgets import toast


class Update(QFrame):
    def __init__(self,toast_provider: toast.QToastProvider, restart, parent=None):
        super().__init__(parent)
        self.setObjectName("update")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.restart = restart

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.release_notes_url = ""
        self.update_package_url = ""
        self.update_package_name = ""
        self.update_running = False

        self.progress_bar = QProgressBar(parent=self)
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedWidth(int(200 * self.scaleFactor))
        self.progress_bar.setTextVisible(False)

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

        self.release_notes_button = QPushButton("Release notes")
        self.release_notes_button.clicked.connect(self.open_notes)
        self.release_notes_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.release_notes_button.hide()
        self.layout.addWidget(self.release_notes_button)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.download_update)
        self.update_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.layout.addWidget(self.update_button)
        self.update_button.hide()

        self.restart_app = QPushButton("Restart application")
        self.restart_app.clicked.connect(self.restart)
        self.restart_app.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.layout.addWidget(self.restart_app)
        self.restart_app.hide()

        self.update_notice = QLabel("Application successfully updated. Changes will take effect after restarting the application.")
        self.update_notice.setStyleSheet(f"font-size: {12 * self.scaleFactor}px;")
        self.update_notice.setWordWrap(True)
        self.layout.addWidget(self.update_notice)
        self.update_notice.hide()

        self.setStyleSheet("""
            #update {
                background-color: #212121;
                border-top-left-radius: 10px;
            }
        """)

        self.hide()

    def update_application(self):
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_bar.raise_()

        with ZipFile(os.path.join("_temp", self.update_package_name), "r") as zip_ref:
            zip_ref.extractall(path="_temp")
        os.remove(os.path.join("_temp", self.update_package_name))

        files = []
        root_dir = "_temp"

        for root, dirs, _files in os.walk(root_dir):
            for fileName in _files:
                file_path = os.path.join(os.path.join(root, fileName))
                files.append(file_path)

        file_list = []
        for i in files:
            if ".zip" not in i and "aether.exe" not in i:
                file_list.append(i)

        target_dir = "test"

        for i in file_list:
            source_path = i
            target_path = i.replace(root_dir, target_dir)
            if os.path.exists(target_path):
                shutil.move(source_path, target_path)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.move(i, target_path)

        os.replace("_temp/aether.exe", "tempfile.exe")
        os.replace("aether.exe", "aether-old.exe")
        os.replace("tempfile.exe", "aether.exe")

        self.restart_app.show()
        self.update_button.hide()

        self.update_notice.show()

        shutil.rmtree("_temp")
        self.update_running = False
        self.progress_bar.hide()
        self.toast_provider.show_toast("Update complete. Restart the application to apply the changes.", variant="success", timeout=10000)

    def download_update(self):
        if self.update_running:
            self.toast_provider.show_toast("An update is already running.", variant="warning")
            return
        self.update_running = True
        self.progress_bar.setMaximum(100)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_bar.raise_()
        if not self.update_package_url:
            self.toast_provider.show_toast("No update package found.", variant="error")
            return
        if not os.path.exists("_temp"):
            os.mkdir("_temp")
        reply = request_helpers.make_request(self.update_package_url)
        file_name = self.update_package_name.split("/")[-1]

        def on_progress(bytes_received, bytes_total):
            pct = bytes_received / bytes_total * 100
            self.progress_bar.setValue(pct)

        def on_finished():
            if reply.error() == reply.NetworkError.NoError:
                self.progress_bar.setMaximum(0)
                data = reply.readAll().data()
                with open(os.path.join("_temp", file_name), "wb") as f:
                    f.write(data)
                self.progress_bar.hide()
                self.update_application()
            else:
                self.update_running = False
                self.progress_bar.hide()
                self.toast_provider.show_toast("Failed to download update package.", variant="error")

            reply.deleteLater()

        reply.downloadProgress.connect(on_progress)
        reply.finished.connect(on_finished)

    def open_notes(self):
        if self.release_notes_url:
            webbrowser.open(self.release_notes_url)

    def check_for_update(self):
        r = request_helpers.make_request(
            url=GITHUB_API
        )
        self.check_for_update_button.setText("Checking for updates...")
        self.check_for_update_button.setDisabled(True)
        def on_req_success():
            self.check_for_update_button.setText("Check for updates")
            self.check_for_update_button.setDisabled(False)
            if r.error() == r.NetworkError.NoError:
                data = bytes(r.readAll())
                body = json.loads(data.decode("utf-8")) if data else {}
                release_tag = body.get("tag_name")
                self.latest_version = release_tag.removeprefix("v")
                self.latest_version_label.setText(f"Latest version: v{self.latest_version}")
                if release_tag.removeprefix("v") != VERSION:
                    self.release_notes_button.show()
                    self.update_button.show()
                    self.check_for_update_button.hide()
                    self.release_notes_url = body.get("html_url")
                    self.toast_provider.show_toast("An update is available.", timeout=0 if not self.isVisible() else 3000, variant="info")
                    for i in body.get("assets", []):
                        if i.get("content_type") == "application/x-zip-compressed":
                            self.update_package_url = i.get("browser_download_url")
                            self.update_package_name = i.get("name")
                            break
                    else:
                        self.toast_provider.show_toast("No update package found.", variant="error")
                else:
                    if self.isVisible():
                        self.toast_provider.show_toast("You are already using the latest version.", variant="success")

            else:
                self.toast_provider.show_toast("Failed to check for updates.", variant="error")

            r.deleteLater()
        r.finished.connect(on_req_success)

    def resizeEvent(self, event):
        self.progress_bar.move((self.width() // 2) - (self.progress_bar.width() // 2), self.height() - self.progress_bar.height())

    def open(self):
        self.show()
        self.raise_()