from PySide6.QtGui import QIcon, Qt, QGuiApplication, QFont
from PySide6.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QEvent
from widgets import title_bar, tray_menu, settings, sidebar, body, toast
from widgets.popups import add_pack


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Storeß Desktop")

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

        self.screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.screen.devicePixelRatio()
        self.resize(int(400 * self.scaleFactor), int(300 * self.scaleFactor))
        self.setFixedSize(self.size())

        self.toast_provider = toast.QToastProvider(parent=self)
        self.toast_provider.resize(self.size())
        self.toast_provider.show()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('utils/icon.png'))
        self.tray_icon.setToolTip("Storeß Desktop")
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
        self.title_bar.settings_button.clicked.connect(self.toggle_settings)
        self.title_bar.setFixedHeight(int(round(35 * self.scaleFactor)))
        self.central_layout.addWidget(self.title_bar)

        self.body = QWidget()
        self.central_layout.addWidget(self.body)

        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body.setLayout(self.body_layout)

        self.main = body.Body(toast_provider=self.toast_provider, main_window=self)

        self.add_pack_widget = add_pack.AddPack(parent=self.central_widget, body_widget=self.main)
        self.add_pack_widget.move((self.width() - self.add_pack_widget.width()) // 2, (self.height() - self.add_pack_widget.height()) // 2)

        self.sidebar = sidebar.Sidebar(body_widget=self.main, add_pack_widget=self.add_pack_widget)
        self.body_layout.addWidget(self.sidebar)

        self.add_pack_widget.sidebar_widget = self.sidebar

        self.main.sidebar = self.sidebar

        self.body_layout.addWidget(self.main)
        self.window_visible = False

        base_size = 10
        scaled_font = QFont()
        scaled_font.setPointSizeF(base_size * self.scaleFactor)

        self.setFont(scaled_font)

        self.setStyleSheet("""
            #central_widget {
                background-color: #212121;
                border-top-left-radius: 10px;
            }
            QWidget {
                color: #ccc;
            }
        """)

        self.settings_widget = settings.Settings(self.toast_provider, parent=self.central_widget)

    def toggle_settings(self):
        if self.settings_widget.settings_open:
            self.settings_widget.settings_open = False
            self.settings_widget.setVisible(False)
        else:
            self.settings_widget.settings_open = True
            self.settings_widget.setVisible(True)

    def handle_tray_click(self):
        if self.window_visible:
            self.hide()
        else:
            self.make_visible()
        self.window_visible = not self.window_visible

    def make_visible(self):
        screen_rectangle = self.screen.availableGeometry()
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
            if not self.isActiveWindow():
                self.window_visible = False
                self.hide()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    app.exec()
