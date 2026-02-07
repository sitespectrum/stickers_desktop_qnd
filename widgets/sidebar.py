import ctypes
import json

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QScrollArea

from globals.user import user
from globals.constants import SERVER
from modules import request_helpers


class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.current_user = user
        self.current_user.logged_inChanged.connect(self.get_sticker_packs)
        self.scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

        self._thumbnail_cache: dict[str, QIcon] = {}
        self._pending_thumbnail: dict[object, QPushButton] = {}

        self.setObjectName("sidebar")
        self.setFixedWidth(40 * self.scaleFactor)
        self.setStyleSheet("""
           QFrame#sidebar {
               border-right: 1px solid #333;
               background-color: transparent;
           }
        """)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.scroll = QScrollArea(self)
        self.scroll.setStyleSheet("background-color: transparent;")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll.setWidget(self.scroll_content)

        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(1 * self.scaleFactor)

        self.layout.addWidget(self.scroll)

    def _clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _fetch_thumbnail_into_button(self, thumbnail_id: str, button: QPushButton):
        if not thumbnail_id:
            return

        url = f"{SERVER}/api/stickers/get_sticker/{thumbnail_id}"
        if url in self._thumbnail_cache:
            button.setIcon(self._thumbnail_cache[url])
            button.setIconSize(button.size())
            return

        reply = request_helpers.make_request(url)
        self._pending_thumbnail[reply] = button

        def on_finished():
            btn = self._pending_thumbnail.pop(reply, None)
            if btn is not None and reply.error() == reply.NetworkError.NoError:
                # noinspection PyTypeChecker
                data = bytes(reply.readAll())
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    icon = QIcon(pixmap)
                    self._thumbnail_cache[url] = icon
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(30 * self.scaleFactor, 30 * self.scaleFactor))
            reply.deleteLater()

        reply.finished.connect(on_finished)

    def get_sticker_packs(self):
        self._clear_layout()
        if not self.current_user.logged_in:
            return

        url = f"{SERVER}/api/stickers/get_packs"
        reply = request_helpers.make_request(url)

        def on_finished():
            try:
                if reply.error() != reply.NetworkError.NoError:
                    return
                data = bytes(reply.readAll())
                payload = json.loads(data.decode("utf-8")) if data else {}
                for pack in payload.get("packs", []):
                    button = QPushButton("")
                    button.setFixedSize(35 * self.scaleFactor, 35 * self.scaleFactor)
                    button.setCursor(Qt.CursorShape.PointingHandCursor)
                    button.setStyleSheet("""
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
                    button.clicked.connect(lambda checked=False, name=pack["name"]: print(name))
                    self.content_layout.addWidget(button)

                    self._fetch_thumbnail_into_button(str(pack.get("thumbnail_id", "")), button)
            finally:
                reply.deleteLater()

        reply.finished.connect(on_finished)
