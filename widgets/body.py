import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar

from widgets.popups import pack_not_downloaded, download_failed
from modules import download_pack


class Body(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("body")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.current_pack = ""
        self.pack_not_downloaded = pack_not_downloaded.PackNotDownloaded(parent=self)

        self.progress_bar = QProgressBar(parent=self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedSize(int(200 * self.scaleFactor), int(20 * self.scaleFactor))
        self.progress_bar.setRange(0, 100)

        self.downloader = download_pack.DownloadPack()
        self.downloader.download_failed.connect(self.on_download_fail)
        self.downloader.pack_downloaded.connect(self.load_stickers)
        self.downloader.percent_changed.connect(self.on_progress)

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
                width: 4px;
                border-radius: 2px;
                margin: 0.5px;
            }
        """)

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.welcome = QLabel("Welcome back! To begin, select a sticker pack from the left.")
        self.layout.addWidget(self.welcome)

        self.setLayout(self.layout)

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

    def download_pack(self, pack: str = ""):
        if not os.path.exists(os.path.join(os.getcwd(), "stickers", pack)):
            if not os.path.exists(os.path.join(os.getcwd(), "stickers")):
                os.mkdir(os.path.join(os.getcwd(), "stickers"))
            os.mkdir(os.path.join(os.getcwd(), "stickers", pack))
            self.downloader.download_pack(pack)
        else:
            print("Pack already downloaded")
        self.load_stickers(pack)

    def load_stickers(self, sticker_pack: str):
        if self.downloader.downloading:
            return
        self.pack_not_downloaded.setVisible(False)
        self.current_pack = sticker_pack
        self._clear_layout()
        if not os.path.exists(os.path.join(os.getcwd(), "stickers", sticker_pack)):
            self.pack_not_downloaded.setVisible(True)
            # noinspection PyBroadException
            try:
                self.pack_not_downloaded.download_button.clicked.disconnect()
            except Exception:
                pass
            self.pack_not_downloaded.download_button.clicked.connect(lambda checked=False, pack=sticker_pack: self.download_pack(pack))
            self.pack_not_downloaded.raise_()
        pass

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

        super().resizeEvent(event)
