import hashlib
import json
import uuid
import webbrowser

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton

from modules import ui_helpers, handle_oauth_login, request_helpers
from globals import user
from globals.constants import SERVER
from widgets import toast


class Settings(QFrame):
    def __init__(self,toast_provider: toast.QToastProvider , parent=None):
        super().__init__(parent)
        self.current_user = user.user
        self.current_user.logged_inChanged.connect(self.set_user)
        self.server_running = False
        self.setObjectName("settings")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.toast_provider = toast_provider

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setFixedSize(int(400 * self.scaleFactor), int(300 * self.scaleFactor))
        self.setStyleSheet("""
            QWidget {
                color: #ccc;
            }
            #settings {
                background-color: #212121;
                border-top-left-radius: 10px;
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
        self.close_button.setFixedSize(btn_px, btn_px)
        self.close_button.clicked.connect(self.close_settings)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setIcon(ui_helpers.svg_to_icon("utils/ui/x.svg", QSize(icon_px, icon_px), button_color))
        self.close_button.setIconSize(QSize(icon_px, icon_px))

        self.user_label = QLabel("Not logged in")
        self.user_label.setStyleSheet(f"font-size: {12 * self.scaleFactor}px;")

        self.login_button = QPushButton("Login")
        self.login_button.setFixedSize(int(100 * self.scaleFactor), int(20 * self.scaleFactor))
        self.login_button.clicked.connect(self.start_login)

        self.title = QLabel("Settings")
        self.title.setStyleSheet(f"font-size: {20 * self.scaleFactor}px; font-weight: bold;")
        self.layout.addWidget(self.close_button)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.user_label)
        self.layout.addWidget(self.login_button)

        self.server_thread = handle_oauth_login.OAuthServerThread()
        handle_oauth_login.OAuthHandler.thread_ref = self.server_thread
        self.server_thread.server_started.connect(self.on_server_ready)

        self.wait_thread = None

        self.pkce_verifier = None
        self.challenge = None

        self.get_user()

    def set_user(self, logged_in: bool = False):
        if logged_in:
            self.user_label.setText(f"Logged in as <b>{"@" + self.current_user.username if not self.current_user.username else self.current_user.display_name}</b>")
            try:
                self.login_button.clicked.disconnect()
            except RuntimeWarning:
                pass
            self.login_button.clicked.connect(self.log_out)
            self.login_button.setText("Logout")
        else:
            try:
                self.login_button.clicked.disconnect()
            except RuntimeWarning:
                pass
            self.login_button.clicked.connect(self.start_login)
            self.user_label.setText("Not logged in")
            self.login_button.setText("Login")

    def log_out(self):
        r = request_helpers.make_request(url=f"{SERVER}/api/auth/logout")
        self.login_button.setText("Logging out...")
        self.login_button.setDisabled(True)

        def req_finished():
            self.login_button.setDisabled(False)
            if r.error() == r.NetworkError.NoError:
                self.current_user.logged_in = False
                self.toast_provider.show_toast("Logged out successfully", variant="success")
            r.deleteLater()

        r.finished.connect(req_finished)

    def get_user(self):
        r = request_helpers.make_request(url=f"{SERVER}/api/auth/profile/me")

        def req_finished():
            if r.error() == r.NetworkError.NoError:
                data = bytes(r.readAll())
                body = json.loads(data.decode("utf-8")) if data else {}
                self.current_user.username = body["username"]
                self.current_user.display_name = body["display_name"]
                self.current_user.role = body["role"]
                self.current_user.logged_in = True
            elif r.error() == r.NetworkError.ConnectionRefusedError:
                self.current_user.logged_in = False
                self.toast_provider.show_toast("Failed to connect to server. Continuing in offline mode", variant="error", timeout=5000)
            else:
                self.current_user.logged_in = False
            r.deleteLater()

        r.finished.connect(req_finished)

    def on_server_ready(self, redirect_uri):
        webbrowser.open(f"{SERVER}/login?send_to={redirect_uri}&challenge={self.challenge}")

    def on_code_received(self, code: str):
        self.server_running = True
        self.start_login()

        if code == handle_oauth_login.OAuthHandler.ABORT_CODE:
            return

        r = request_helpers.make_request(
            url=f"{SERVER}/api/auth/oauth/validate_code",
            method="POST",
            json_data={"code": code, "code_verifier": self.pkce_verifier}
        )

        def req_finished():
            if r.error() == r.NetworkError.NoError:
                self.get_user()
            else:
                self.toast_provider.show_toast("Failed to login", variant="error")
            r.deleteLater()

        r.finished.connect(req_finished)

    def close_settings(self):
        self.setVisible(False)
        self.settings_open = False

    def start_login(self):
        if not self.server_running:
            handle_oauth_login.OAuthHandler.code = None

            self.pkce_verifier = uuid.uuid4().hex
            self.challenge = hashlib.sha256(self.pkce_verifier.encode()).hexdigest()

            self.login_button.setText("Abort")
            self.server_thread.start()
            self.server_running = True

            self.wait_thread = handle_oauth_login.OAuthWaitThread()
            self.wait_thread.code_received.connect(self.on_code_received)
            self.wait_thread.start()
        else:
            self.login_button.setText("Login")
            self.server_thread.stop()
            self.server_thread.quit()
            self.server_thread.wait()
            self.server_running = False
