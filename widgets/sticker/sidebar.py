import glob
import json
import os

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QScrollArea, QMenu

from globals.user import user
from globals.constants import SERVER
from modules import request_helpers, ui_helpers
from modules.ui_helpers import svg_to_icon
from widgets import toast

from widgets.sticker import body, sticker_pack_menu
from widgets.sticker.popups import add_pack


class Sidebar(QFrame):
    def __init__(self, toast_provider: toast.QToastProvider, load_favourites, body_widget: body.Body = None, add_pack_widget: add_pack.AddPack=None):
        super().__init__()
        self.current_user = user
        self.current_user.logged_inChanged.connect(self.get_sticker_packs)
        self.scaleFactor = ui_helpers.get_screen_scale()

        self.load_favourites = load_favourites

        self.toast_provider = toast_provider

        self.user_packs = []

        self.body = body_widget
        self.add_pack_widget = add_pack_widget

        self._thumbnail_cache: dict[str, QIcon] = {}
        self._pending_thumbnail: dict[object, QPushButton] = {}

        self.pack_context_menu = sticker_pack_menu.PackMenu(parent=self)

        self.setObjectName("sidebar")
        self.setFixedWidth(int(40 * self.scaleFactor))
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
        self.content_layout.setSpacing(int(1 * self.scaleFactor))

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
            reply.deleteLater()

        reply.finished.connect(on_finished)

    def add_pack(self, pack_name: str = ""):
        if not pack_name:
            self.add_pack_widget.open_popup()
            self.add_pack_widget.raise_()
            return
        r = request_helpers.make_request(f"{SERVER}/api/stickers/add_pack", "POST", json_data={"pack_name": pack_name})
        def on_req_finished():
            if r.error() != r.NetworkError.NoError:
                self.toast_provider.show_toast("Failed to add pack", variant="error")
                return
            self.toast_provider.show_toast("Pack added to your profile", variant="success")
            self.get_sticker_packs()

        r.finished.connect(on_req_finished)

    def remove_pack(self, pack_name: str = ""):
        if not pack_name:
            return
        r = request_helpers.make_request(f"{SERVER}/api/stickers/remove_pack/{pack_name}", "DELETE")
        def on_req_finished():
            if r.error() != r.NetworkError.NoError:
                self.toast_provider.show_toast("Failed to remove pack", variant="error")
                return
            self.toast_provider.show_toast("Pack removed from your profile", variant="success")
            self.get_sticker_packs()

        r.finished.connect(on_req_finished)


    def pack_context_menu_requested(self, pos, button, pack):
        self.pack_context_menu.download.setVisible(True)
        try:
            self.pack_context_menu.download.triggered.disconnect()
        except (TypeError, RuntimeError, RuntimeWarning):
            pass
        self.pack_context_menu.download.triggered.connect(lambda checked=False, pack=pack: self.body.download_pack(pack, no_switch=True))
        self.pack_context_menu.redownload.setVisible(True)
        try:
            self.pack_context_menu.redownload.triggered.disconnect()
        except (TypeError, RuntimeError, RuntimeWarning):
            pass
        self.pack_context_menu.redownload.triggered.connect(lambda checked=False, pack=pack: self.body.redownload_pack(pack))
        self.pack_context_menu.delete_action.setVisible(True)
        try:
            self.pack_context_menu.delete_action.triggered.disconnect()
        except (TypeError, RuntimeError, RuntimeWarning):
            pass
        self.pack_context_menu.delete_action.triggered.connect(lambda checked=False, pack=pack: self.body.delete_pack(pack))
        self.pack_context_menu.remove_action.setVisible(True)
        self.pack_context_menu.add_action.setVisible(True)
        try:
            self.pack_context_menu.add_action.triggered.disconnect()
        except (TypeError, RuntimeError, RuntimeWarning):
            pass
        try:
            self.pack_context_menu.remove_action.triggered.disconnect()
        except (TypeError, RuntimeError, RuntimeWarning):
            pass

        if pack not in self.user_packs:
            self.pack_context_menu.remove_action.setVisible(False)
            self.pack_context_menu.add_action.setVisible(True)
            self.pack_context_menu.add_action.triggered.connect(
                lambda checked=False, pack=pack: self.add_pack(pack)
            )
        else:
            self.pack_context_menu.add_action.setVisible(False)
            self.pack_context_menu.remove_action.setVisible(True)
            self.pack_context_menu.remove_action.triggered.connect(
                lambda checked=False, pack=pack: self.remove_pack(pack)
            )

        if not self.current_user.logged_in:
            self.pack_context_menu.add_action.setVisible(False)
            self.pack_context_menu.remove_action.setVisible(False)

        global_pos = button.mapToGlobal(QPoint(0, button.height()))
        self.pack_context_menu.move(global_pos)

        if os.path.exists(os.path.join("stickers", pack)):
            self.pack_context_menu.download.setVisible(False)
        else:
            self.pack_context_menu.redownload.setVisible(False)
            self.pack_context_menu.delete_action.setVisible(False)

        self.pack_context_menu.show()

    def add_manage_buttons(self):

        button_color = QColor("#E6E6E6")

        add_button = QPushButton()
        add_button.setFixedSize(int(35 * self.scaleFactor), int(20 * self.scaleFactor))
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #111;
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
        add_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "plus.svg"), QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)), button_color))
        add_button.clicked.connect(lambda checked=False: self.add_pack())

        manage_favourites_menu = QMenu()
        manage_favourites_menu.setStyleSheet("""
            QMenu {
                background-color: #111;
                border-radius: 6px;
                padding: 0;
                margin: 0;
            }

            QMenu::item {
                color: #ccc;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background-color: #333;
            }

            QMenu::item:pressed {
                background-color: #444;
            }

            QMenu::separator {
                height: 1px;
                background: #222;
                margin: 4px 0;
            }
        """)
        manage_favourites_menu.addAction("Refresh from profile", lambda checked=False: self.body.download_favourites())

        favourites_button = QPushButton()
        favourites_button.setFixedSize(int(35 * self.scaleFactor), int(20 * self.scaleFactor))
        favourites_button.setCursor(Qt.CursorShape.PointingHandCursor)
        favourites_button.setStyleSheet("""
            QPushButton {
                        background-color: #111;
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
        favourites_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "heart.svg"), QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)), button_color))
        favourites_button.clicked.connect(lambda checked=False: self.load_favourites())
        favourites_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        favourites_button.customContextMenuRequested.connect(lambda pos: manage_favourites_menu.exec(favourites_button.mapToGlobal(pos)))


        refresh_button = QPushButton()
        refresh_button.setFixedSize(int(35 * self.scaleFactor), int(20 * self.scaleFactor))
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.setStyleSheet("""
                    QPushButton {
                        background-color: #111;
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
        refresh_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "refresh.svg"),
                                       QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)), button_color))
        refresh_button.clicked.connect(self.get_sticker_packs)

        separator = QWidget()
        separator.setFixedHeight(int(1 * self.scaleFactor))
        separator.setStyleSheet("background-color: #333;")
        self.content_layout.addSpacing(int(5 * self.scaleFactor))
        self.content_layout.addWidget(separator)
        self.content_layout.addSpacing(int(5 * self.scaleFactor))
        if self.current_user.logged_in:
            self.content_layout.addWidget(favourites_button)
            self.content_layout.addSpacing(int(2 * self.scaleFactor))
        self.content_layout.addWidget(add_button)
        self.content_layout.addSpacing(int(2 * self.scaleFactor))
        self.content_layout.addWidget(refresh_button)

    def get_sticker_packs(self):
        self.user_packs = []
        self._clear_layout()

        def load_local_packs(packs):
            for pack in packs:
                if pack == "favourites":
                    continue
                with open(os.path.join("stickers", pack, "info.json"), "r") as f:
                    info = json.loads(f.read())
                button = QPushButton("")
                button.setFixedSize(int(35 * self.scaleFactor), int(35 * self.scaleFactor))
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
                button.clicked.connect(lambda checked=False, name=pack: self.body.load_stickers(name))
                self.content_layout.addWidget(button)
                thumbnail = glob.glob(f"./stickers/{pack}/thumbnail.*")
                button.setIcon(QIcon(thumbnail[0]))
                button.setIconSize(QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)))

                button.setToolTip(info["title"])

                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, btn=button, pack=pack: self.pack_context_menu_requested(pos, btn, pack)
                )

        if not self.current_user.logged_in:
            packs = []
            if not os.path.exists(os.path.join("stickers")):
                pass
            else:
                packs = os.listdir(os.path.join("stickers"))
                load_local_packs(packs)
            self.add_manage_buttons()

        else:
            url = f"{SERVER}/api/stickers/get_packs"
            reply = request_helpers.make_request(url)

            def on_finished():
                try:
                    if reply.error() != reply.NetworkError.NoError:
                        self.toast_provider.show_toast("Failed to fetch packs", variant="error")
                        return
                    data = bytes(reply.readAll())
                    payload = json.loads(data.decode("utf-8")) if data else {}
                    self.user_packs = [i["name"] for i in payload.get("packs", [])]
                    for pack in payload.get("packs", []):
                        button = QPushButton("")
                        button.setFixedSize(int(35 * self.scaleFactor), int(35 * self.scaleFactor))
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
                        button.clicked.connect(lambda checked=False, name=pack["name"]: self.body.load_stickers(name))
                        self.content_layout.addWidget(button)
                        thumbnail = glob.glob(f"./stickers/{pack['name']}/thumbnail.*")
                        if not thumbnail:
                            button.setToolTip(pack["title"])
                            button.setIcon(svg_to_icon(os.path.join("utils", "ui", "ellipsis.svg"), QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)), QColor("#E6E6E6")))
                            self._fetch_thumbnail_into_button(str(pack.get("thumbnail_id", "")), button)
                        else:
                            button.setIcon(QIcon(thumbnail[0]))
                            with open(os.path.join("stickers", pack["name"], "info.json"), "r") as f:
                                info = json.loads(f.read())
                            button.setToolTip(info["title"])
                        button.setIconSize(QSize(int(30 * self.scaleFactor), int(30 * self.scaleFactor)))

                        button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                        button.customContextMenuRequested.connect(
                            lambda pos, btn=button, pack=pack["name"]: self.pack_context_menu_requested(pos, btn, pack)
                        )
                    if os.path.exists("stickers"):
                        local_packs = [i for i in os.listdir("stickers") if i not in [i["name"] for i in payload.get("packs", [])] and i != "favourites"]
                        if local_packs:
                            separator = QWidget()
                            separator.setFixedHeight(int(1 * self.scaleFactor))
                            separator.setStyleSheet("background-color: #333;")
                            self.content_layout.addSpacing(int(5 * self.scaleFactor))
                            self.content_layout.addWidget(separator)
                            self.content_layout.addSpacing(int(5 * self.scaleFactor))

                            packs = local_packs
                            load_local_packs(packs)
                    self.add_manage_buttons()
                finally:
                    reply.deleteLater()

            reply.finished.connect(on_finished)
