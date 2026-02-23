import json
import os
import shutil

from PySide6.QtCore import Qt, QSize, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QScrollArea, QWidget, \
    QApplication, QGraphicsBlurEffect

from caches.sticker_icon_cache import StickerIconCache
from globals.constants import SERVER
from globals.user import user
from widgets import toast
from widgets.sticker import sticker_preview
from widgets.popups import pack_not_downloaded, download_failed
from modules import download_pack, request_helpers, clipboard


def get_rel_pos(widget, parent, main_window):
    # Get the widget's position relative to the scrollbar
    global_position_widget = widget.mapToGlobal(QPoint(0, 0))
    local_position_widget = parent.mapFromGlobal(global_position_widget)

    # Get the scrollbar's position relative to the main window
    global_position_scrollbar = parent.mapToGlobal(QPoint(0, 0))
    local_position_scrollbar = main_window.mapFromGlobal(global_position_scrollbar)

    # Combine the positions to get the widget's position relative to the main window
    position_relative_to_main_window = local_position_scrollbar + local_position_widget
    return position_relative_to_main_window


class Body(QFrame):
    def __init__(self, toast_provider: toast.QToastProvider, main_window=None):
        super().__init__()
        self.setObjectName("body")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.icon_cache = StickerIconCache(max_size=500)

        self.toast_provider = toast_provider

        self.current_pack = ""
        self.pack_not_downloaded = pack_not_downloaded.PackNotDownloaded(parent=self)

        self.progress_bar = QProgressBar(parent=self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedSize(int(200 * self.scaleFactor), int(20 * self.scaleFactor))
        self.progress_bar.setRange(0, 100)

        self.downloader = download_pack.DownloadPack()
        self.downloader.download_failed.connect(self.on_download_fail)
        self.downloader.percent_changed.connect(self.on_progress)

        self.main_window = main_window
        self.preview_sticker_widget = sticker_preview.PreviewSticker(self, parent=self.main_window)
        self.preview_sticker_widget.customContextMenuRequested.connect(self.close_sticker_preview)

        self.preview_open = False

        self.sidebar = None

        self.blur_effect = QGraphicsBlurEffect(self)
        self.setGraphicsEffect(self.blur_effect)
        self.blur_effect.setBlurRadius(0)

        self.blur_in_effect = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_in_effect.setDuration(250)
        self.blur_in_effect.setStartValue(0)
        self.blur_in_effect.setEndValue(20)
        self.blur_in_effect.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.blur_out_effect = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_out_effect.setDuration(250)
        self.blur_out_effect.setStartValue(20)
        self.blur_out_effect.setEndValue(0)
        self.blur_out_effect.setEasingCurve(QEasingCurve.Type.InCubic)

        self.download_failed = download_failed.DownloadFailed(parent=self)

        self.setStyleSheet("""
            #body {
                background-color: transparent;
            }
            QProgressBar {
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
            }
            QProgressBar::chunk {
                background-color: #333;
                border-radius: 2px;
                margin: 0.5px;
            }
        """)

        self.base_layout = QVBoxLayout()
        self.setLayout(self.base_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setViewportMargins(0, 0, 0, 0)
        self.scroll_area.viewport().setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                width: 5px;
            }
            QScrollBar::handle::vertical {
                background: #333;
                border-radius: 2px;
                border: none;
            }
            QScrollBar::handle::vertical::pressed {
                background: #444;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #000;
                border-radius: 2px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea QWidget {
                background: transparent;
                border: none;
            }
            QPushButton { 
                background-color: transparent; 
                border: none; 
                border-radius: 5px;
            } 
            QPushButton:hover { 
                background-color: #333; 
            }
            QPushButton:pressed { 
                background-color: #444; 
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.scroll_content)
        self.base_layout.addWidget(self.scroll_area)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.welcome = QLabel("Welcome back! To begin, select a sticker pack from the left.")
        self.layout.addWidget(self.welcome)

        self.current_user = user
        self.current_user.logged_inChanged.connect(self._clear_layout)

    def close_sticker_preview(self):
        self.preview_open = False
        self.blur_out_effect.start()
        self.preview_sticker_widget.close_preview()

    def preview_sticker(self, pos: QPoint, button: QPushButton, pack: str, sticker: str):
        self.preview_open = True
        self.blur_in_effect.start()
        self.preview_sticker_widget.show_preview(button.icon(), pack, sticker, start_pos=get_rel_pos(button, self.scroll_area, self))
        self.toast_provider.raise_()

    def copy_sticker(self, pack: str, sticker: str):
        clipboard.copy_image(os.path.join("stickers", pack, sticker))
        self.toast_provider.show_toast("Copied sticker to clipboard")

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def on_progress(self, progress):
        if progress == 100:
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.raise_()
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)

    def on_download_fail(self, failed):
        if not failed:
            return
        if os.path.exists(os.path.join(os.getcwd(), "stickers", self.current_pack)):
            os.rmdir(os.path.join(os.getcwd(), "stickers", self.current_pack))
            self.load_stickers(self.current_pack)
            self.download_failed.show()
            self.download_failed.description.setText(failed)
            self.download_failed.raise_()

    def download_pack(self, pack: str = "", no_switch=False, add=False, refresh_sidebar=False, close_popup=None):
        if self.downloader.downloading:
            self.toast_provider.show_toast("Another pack is already downloading", variant="warning", timeout=1500)
            return
        if not os.path.exists(os.path.join(os.getcwd(), "stickers", pack)):
            if not os.path.exists(os.path.join(os.getcwd(), "stickers")):
                os.mkdir(os.path.join(os.getcwd(), "stickers"))

            r = request_helpers.make_request(f"{SERVER}/api/stickers/get_pack/{pack}" if not add else f"{SERVER}/api/stickers/get_pack/{pack}?add=true")
            os.mkdir(os.path.join(os.getcwd(), "stickers", pack))
            def create_sticker_into():
                if r.error() != r.NetworkError.NoError:
                    shutil.rmtree(os.path.join(os.getcwd(), "stickers", pack))
                if r.error() == r.NetworkError.ContentNotFoundError:
                    self.toast_provider.show_toast("Pack not found", variant="error")
                    return
                if close_popup is not None:
                    close_popup()
                data = bytes(r.readAll())
                payload = json.loads(data.decode("utf-8")) if data else {}
                with open(os.path.join(os.getcwd(), "stickers", pack, "info.json"), "w") as f:
                    f.write(json.dumps(payload, indent=4))
            r.finished.connect(create_sticker_into)
            self.downloader.pack_downloaded.disconnect()
            if not no_switch:
                self.downloader.pack_downloaded.connect(self.load_stickers)
            if refresh_sidebar:
                self.downloader.pack_downloaded.connect(self.sidebar.get_sticker_packs)
            self.downloader.download_pack(pack)
        else:
            self.toast_provider.show_toast("This pack is already downloaded", variant="warning")
        if self.current_pack == pack:
            self.load_stickers(pack)

    def delete_pack(self, pack: str):
        with open(os.path.join(os.getcwd(), "stickers", pack, "info.json"), "r") as f:
            payload = json.loads(f.read())
            pack_title = payload["title"]
        shutil.rmtree(os.path.join(os.getcwd(), "stickers", pack))
        self.toast_provider.show_toast(f"Deleted local files for pack {pack_title}")
        if pack == self.current_pack:
            self.load_stickers(pack)

        if self.sidebar is not None:
            self.sidebar.get_sticker_packs()

    def redownload_pack(self, pack: str):
        shutil.rmtree(os.path.join(os.getcwd(), "stickers", pack))
        self.download_pack(pack, no_switch=True)

    def load_stickers(self, sticker_pack: str):
        if self.downloader.downloading:
            return

        if self.preview_open:
            self.close_sticker_preview()

        self.pack_not_downloaded.setVisible(False)
        self.current_pack = sticker_pack
        self._clear_layout()

        folder = os.path.join("stickers", sticker_pack)

        if not os.path.exists(folder):
            self.pack_not_downloaded.setVisible(True)
            try:
                self.pack_not_downloaded.download_button.clicked.disconnect()
            except Exception:
                pass
            self.pack_not_downloaded.download_button.clicked.connect(
                lambda checked=False, pack=sticker_pack: self.download_pack(pack)
            )
            self.pack_not_downloaded.raise_()
            return

        def get_order(filename):
            return int(filename.split("_")[0])

        files = sorted(
            [f for f in os.listdir(folder) if f != "info.json" and "thumbnail" not in f],
            key=get_order
        )

        if not files:
            self.toast_provider.show_toast("This pack is empty", variant="warning")
            return

        max_value = 100
        chunk_size = max_value / len(files)
        current_value = 0

        button_size = int(50 * self.scaleFactor)
        col_max = max(1, self.scroll_content.width() // button_size)

        row, col = 0, 0

        self.scroll_content.setUpdatesEnabled(False)

        for file in files:
            self.on_progress(current_value)
            QApplication.processEvents()
            if col >= col_max:
                col = 0
                row += 1

            button = QPushButton()
            button.setFixedSize(button_size, button_size)
            button.setIcon(self.icon_cache.get_icon(os.path.join(folder, file)))
            button.setIconSize(QSize(int(45 * self.scaleFactor), int(45 * self.scaleFactor)))
            button.clicked.connect(lambda checked=False, pack=sticker_pack, file=file: self.copy_sticker(pack, file))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, button=button, pack=sticker_pack, file=file: self.preview_sticker(pos, button, pack, file))
            self.layout.addWidget(button, row, col)

            col += 1
            current_value += chunk_size
        self.on_progress(100)
        self.scroll_content.setUpdatesEnabled(True)
        self.scroll_content.update()

        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def resizeEvent(self, event):
        child = self.pack_not_downloaded
        x = (self.width() - child.width()) // 2
        y = (self.height() - child.height()) // 2
        child.move(x, y)

        child = self.download_failed
        x = (self.width() - child.width()) // 2
        y = (self.height() - child.height()) // 2
        child.move(x, y)

        child = self.progress_bar
        x = (self.width() - child.width()) // 2
        y = (self.height() - child.height())
        child.move(x, y)

        self.preview_sticker_widget.resize(self.size())
        self.preview_sticker_widget.move(get_rel_pos(self, self.main_window, self.main_window))

        super().resizeEvent(event)
