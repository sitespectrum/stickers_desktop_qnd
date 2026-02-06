import webbrowser

from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QEvent
import ctypes
from widgets import title_bar, tray_menu
from modules import handle_oauth_login

SERVER = "http://localhost/"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stickerβ")

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

        self.scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        self.resize(400 * self.scaleFactor, 300 * self.scaleFactor)
        self.setFixedSize(self.size())

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('utils/icon.png'))
        self.tray_icon.setToolTip("Tele-py")
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.handle_tray_click)

        self.tray_menu = tray_menu.TrayMenu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_menu.quit_action.triggered.connect(QApplication.quit)

        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)

        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(self.central_layout)

        self.title_bar = title_bar.TitleBar()
        self.title_bar.close_button.clicked.connect(self.close)
        self.title_bar.settings_button.clicked.connect(self.start_login)
        self.title_bar.setFixedHeight(30 * self.scaleFactor)
        self.central_layout.addWidget(self.title_bar)

        self.body = QWidget()
        self.central_layout.addWidget(self.body)

        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body.setLayout(self.body_layout)

        self.sidebar = QWidget()
        self.sidebar.setStyleSheet("border-right: 1px solid #333")
        self.sidebar.setFixedWidth(40 * self.scaleFactor)
        self.body_layout.addWidget(self.sidebar)

        self.main = QWidget()
        self.body_layout.addWidget(self.main)

        self.window_visible = False
        self.server_running = False

        self.server_thread = handle_oauth_login.OAuthServerThread()
        handle_oauth_login.OAuthHandler.thread_ref = self.server_thread
        self.server_thread.server_started.connect(self.on_server_ready)

        self.setStyleSheet("""
            #central_widget {
                background-color: #212121;
                border-top-left-radius: 10px;
            }
        """)

    def on_server_ready(self, redirect_uri):
        webbrowser.open(f"{SERVER}login?send_to={redirect_uri}")

    def start_login(self):
        if not self.server_running:
            self.server_thread.start()
            self.server_running = True
        else:
            self.server_thread.stop()
            self.server_thread.quit()
            self.server_thread.wait()
            self.server_running = False

    def handle_tray_click(self):
        if self.window_visible:
            self.hide()
        else:
            self.make_visible()
        self.window_visible = not self.window_visible

    def make_visible(self):
        screen_rectangle = self.screen().availableGeometry()
        self.move((screen_rectangle.width() - self.width()), (screen_rectangle.height() - self.height()))
        self.window_visible = True
        self.raise_()
        self.activateWindow()
        self.show()

    def closeEvent(self, event):
        self.hide()
        self.window_visible = False
        event.ignore()

    # noinspection PyUnresolvedReferences
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and self.window_visible:
                self.window_visible = False
                self.hide()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    app.exec()
