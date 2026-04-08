import os
import subprocess
import sys
import time
import traceback

from PySide6.QtCore import QEvent, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, Qt, QFont, QGuiApplication
from PySide6.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, \
    QMessageBox, QStackedWidget, QGraphicsOpacityEffect, QLabel

from modules import ui_helpers
from modules.ui_helpers import svg_to_icon
from widgets import title_bar, tray_menu, toast, menu
from widgets.bookmark import body as bookmark_body, edit_bookmark, confirm_delete_bookmark
from widgets.note import body as note_body, edit_note, confirm_delete_note
from widgets.popups import settings
from widgets.sticker import sidebar, body
from widgets.sticker.popups import add_pack


def format_exception(exctype, value, traceback_obj):
    exception_str = '\n' + ''.join(traceback.format_exception(exctype, value, traceback_obj))

    return exception_str


def exception_hook(exctype, value, traceback_obj):
    time_stamp = time.time()
    time_stamp = time.strftime("%Y_%m_%d__%H_%M_%S", time.localtime(time_stamp))
    exception_str = format_exception(exctype, value, traceback_obj)
    if not os.path.exists("reports"):
        os.mkdir("reports")
    with open(f"reports/{time_stamp}.txt", "w") as f:
        f.write(exception_str)

    QMessageBox.critical(None, "Æther Desktop | Error", f"<p>An unexpected error occurred<br>"
                                                        f"<pre>{str(exctype.__name__)}</pre><br>"
                                                        f"The application will quit. Please contact support.<br>"
                                                        f"A detailed error message has been saved here: <br>"
                                                        f"<pre><code>{os.path.abspath(f'reports/{time_stamp}.txt')}</code></pre></p>")

    sys.__excepthook__(exctype, value, traceback_obj)
    app.quit()


def restart_with_new_binary():
    new_exe = os.path.join(os.path.dirname(sys.executable), "aether.exe")
    subprocess.Popen([new_exe])
    time.sleep(0.2)
    QApplication.quit()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Æther Desktop")
        self.setWindowIcon(QIcon(svg_to_icon("utils/aeicon.svg", QSize(100, 100), None)))

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

        self.screen = QGuiApplication.primaryScreen()
        self.scaleFactor = ui_helpers.get_screen_scale()
        self.resize(int(400 * self.scaleFactor), int(300 * self.scaleFactor))
        self.setFixedSize(self.size())

        self.toast_provider = toast.QToastProvider(parent=self)
        self.toast_provider.resize(self.size())
        self.toast_provider.show()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(svg_to_icon("utils/aeicon.svg", QSize(100, 100), None)))
        self.tray_icon.setToolTip("Æther Desktop")
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.handle_tray_click)

        self.tray_menu = tray_menu.TrayMenu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_menu.quit_action.triggered.connect(sys.exit)

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
        self.title_bar.menu_button.toggled.connect(self.toggle_menu)
        self.central_layout.addWidget(self.title_bar)

        self.menu = menu.Menu(stacked_widget_trigger=self.stacked_widget_triggered, parent=self.central_widget)
        self.menu.move(QPoint(0, self.title_bar.height()))
        self.menu.setVisible(False)

        self.body = QWidget()
        self.central_layout.addWidget(self.body)

        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body.setLayout(self.body_layout)

        self.stacked_widget = QStackedWidget()
        self.body_layout.addWidget(self.stacked_widget)

        # Stickers
        self.stickers_frame = QWidget()
        self.stickers_frame.setObjectName("stickers_frame")
        self.stickers_layout = QHBoxLayout()
        self.stickers_frame.setLayout(self.stickers_layout)
        self.stickers_layout.setContentsMargins(0, 0, 0, 0)

        self.stickers_widget = body.Body(toast_provider=self.toast_provider, main_window=self.stickers_frame)

        self.add_pack_widget = add_pack.AddPack(parent=self.stacked_widget, body_widget=self.stickers_widget)
        self.add_pack_widget.resize(self.height() - self.title_bar.height(), self.width())

        self.stickers_sidebar = sidebar.Sidebar(self.toast_provider, self.stickers_widget.load_favourites,
                                                body_widget=self.stickers_widget, add_pack_widget=self.add_pack_widget)
        self.stickers_layout.addWidget(self.stickers_sidebar)

        self.add_pack_widget.sidebar_widget = self.stickers_sidebar

        self.stickers_widget.sidebar = self.stickers_sidebar

        self.stickers_layout.addWidget(self.stickers_widget)

        self.stacked_widget.addWidget(self.stickers_frame)

        # Notes
        self.notes_frame = QWidget()
        self.notes_frame.setObjectName("notes_frame")
        self.notes_layout = QVBoxLayout()
        notes_title = QLabel("Notes")
        notes_title.setStyleSheet(
            f"padding-left: {int(5 * self.scaleFactor)}px; font-size: {int(12 * self.scaleFactor)}px")
        self.notes_layout.addWidget(notes_title)
        self.notes_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_frame.setLayout(self.notes_layout)

        self.confirm_delete_note = confirm_delete_note.ConfirmDeleteNote(parent=self.stacked_widget)
        self.edit_note_widget = edit_note.EditNote(parent=self.stacked_widget)
        self.notes_widget = note_body.Body(self.edit_note_widget, self.confirm_delete_note, self.toast_provider)

        self.notes_layout.addWidget(self.notes_widget)

        self.stacked_widget.addWidget(self.notes_frame)

        # Bookmarks
        self.bookmarks_frame = QWidget()
        self.bookmarks_frame.setObjectName("bookmarks_frame")
        self.bookmarks_layout = QVBoxLayout()
        bookmarks_title = QLabel("Bookmarks")
        bookmarks_title.setStyleSheet(
            f"padding-left: {int(5 * self.scaleFactor)}px; font-size: {int(12 * self.scaleFactor)}px")
        self.bookmarks_layout.addWidget(bookmarks_title)
        self.bookmarks_layout.setContentsMargins(0, 0, 0, 0)
        self.bookmarks_frame.setLayout(self.bookmarks_layout)

        self.confirm_delete_bookmark = confirm_delete_bookmark.ConfirmDeleteBookmark(parent=self.stacked_widget)
        self.edit_bookmark_widget = edit_bookmark.EditBookmark(parent=self.stacked_widget)
        self.bookmarks_widget = bookmark_body.Body(self.edit_bookmark_widget, self.confirm_delete_bookmark,
                                                   self.toast_provider)

        self.bookmarks_layout.addWidget(self.bookmarks_widget)

        self.stacked_widget.addWidget(self.bookmarks_frame)

        self.window_visible = False

        base_size = 10
        scaled_font = QFont()
        scaled_font.setPointSizeF(base_size * self.scaleFactor)

        self.setFont(scaled_font)

        self.setStyleSheet(f"""
            #central_widget {{
                background-color: #212121;
                border-top-left-radius: 10px;
            }}
            QWidget {{
                color: #ccc;
            }}
             QPushButton {{
                background-color: #111;
                border-radius: 5px;
                font-size: {11 * self.scaleFactor}px;
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
            QProgressBar {{
                padding: 3px;
                background-color: #111;
                border-top: 1px solid #333;
                border-left: 1px solid #333;
                border-right: 1px solid #333;
                border-top-right-radius: 5px;
                border-top-left-radius: 5px;
                text-align: center;
                color: transparent;
                height: 30px;
            }}
            QProgressBar::chunk {{
                background-color: #333;
                border-radius: 2px;
                margin: 0.5px;
            }}
            QLineEdit {{
                background-color: transparent;
                border: 1px solid #444;
                border-top-color: transparent;
                border-left-color: transparent;
                border-radius: 3px;
                color: #999999;
                height: 30px;
                padding-left: 1px;
            }}
            QLineEdit:focus {{
                border: 1px solid #444;
            }}
            QPlainTextEdit {{
                background-color: transparent;
                border: 1px solid #444;
                border-top-color: transparent;
                border-left-color: transparent;
                border-radius: 3px;
                color: #999999;
                height: 30px;
                padding-left: 1px;
            }}
            QPlainTextEdit:focus {{
                border-color: #444;
            }}
        """)

        self.settings_widget = settings.Settings(self.toast_provider, restart_with_new_binary,
                                                 parent=self.central_widget)

        self.overlay = QWidget(self.central_widget)
        self.overlay.setGeometry(self.stacked_widget.rect())
        self.overlay.move(0, self.title_bar.height())
        self.overlay.setObjectName("overlay")
        self.overlay.setStyleSheet("background-color: rgba(33, 33, 33, .9);")
        self.overlay.hide()

        # Add this block for opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self.overlay)
        self.opacity_effect.setOpacity(0)
        self.overlay.setGraphicsEffect(self.opacity_effect)

        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(250)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self.overlay.hide)

    def stacked_widget_triggered(self, triggered):
        if self.stickers_widget.preview_open:
            self.stickers_widget.close_sticker_preview()
        if self.notes_widget.note_open:
            self.notes_widget.close_note()
        self.add_pack_widget.close_popup()
        widgets = {
            "stickers": self.stickers_frame,
            "notes": self.notes_frame,
            "bookmarks": self.bookmarks_frame
        }
        self.stacked_widget.setCurrentWidget(widgets[triggered])
        self.title_bar.menu_button.setChecked(False)

    def toggle_menu(self, checked):
        self.menu.raise_()
        if checked:
            self.overlay.show()
            self.fade_in_anim.start()
        else:
            self.fade_out_anim.start()

        self.menu.setVisible(checked)

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
        if self.notes_widget.note_open:
            self.notes_widget.close_note()

        elif self.title_bar.menu_button.isChecked():
            self.title_bar.menu_button.toggle()
        elif self.stickers_sidebar.add_pack_widget.isVisible():
            self.stickers_sidebar.add_pack_widget.close_popup()
        elif self.stickers_widget.preview_open:
            self.stickers_widget.close_sticker_preview()
        else:
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
    sys.excepthook = exception_hook
    window = MainWindow()
    app.exec()
