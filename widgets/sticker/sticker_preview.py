import os
import shutil

import emoji
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PySide6.QtGui import QIcon, QGuiApplication, QColor
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QPushButton, QVBoxLayout, QLabel, QHBoxLayout

from globals.constants import SERVER
from globals.user import user
from modules import request_helpers
from modules.ui_helpers import svg_to_icon


class PreviewSticker(QFrame):
    def __init__(self,body_widget, parent=None):
        super().__init__(parent)

        self.sticker_favourites_name = None
        self.sticker_original_name = None
        self.sticker_pack_name = None

        self.current_user = user

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("preview_sticker")
        self.setStyleSheet("background: rgba(33, 33, 33, .8)")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setVisible(False)

        self.body_widget = body_widget

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.emoji = QLabel()
        self.emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emoji.setStyleSheet(f"font-size: {int(30 * self.scaleFactor)}px; background-color: transparent;")

        self.preview_button = QPushButton()
        self.preview_button.setFixedSize(QSize(int(150 * self.scaleFactor), int(150 * self.scaleFactor)))
        self.preview_button.setIconSize(QSize(int(145 * self.scaleFactor), int(145 * self.scaleFactor)))
        self.preview_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(34, 34, 34, .5);
            }
            QPushButton:pressed {
                background-color: rgba(51, 51, 51, .5);
            }
        """)

        self.add_to_favourites_button = QPushButton()
        self.add_to_favourites_button.clicked.connect(self.add_to_favourites)
        self.add_to_favourites_button.setFixedSize(QSize(int(20 * self.scaleFactor), int(20 * self.scaleFactor)))
        self.add_to_favourites_button.setIconSize(QSize(int(18 * self.scaleFactor), int(18 * self.scaleFactor)))
        self.add_to_favourites_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_to_favourites_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "heart.svg"), QSize(int(18 * self.scaleFactor), int(18 * self.scaleFactor)), QColor("#999")))
        self.add_to_favourites_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(20, 20, 20, .5);
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba(20, 20, 20, .9);
            }}
        """)

        self.remove_from_favourites_button = QPushButton()
        self.remove_from_favourites_button.clicked.connect(self.remove_from_favourites)
        self.remove_from_favourites_button.setFixedSize(QSize(int(20 * self.scaleFactor), int(20 * self.scaleFactor)))
        self.remove_from_favourites_button.setIconSize(QSize(int(18 * self.scaleFactor), int(18 * self.scaleFactor)))
        self.remove_from_favourites_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_from_favourites_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "heart-off.svg"), QSize(int(18 * self.scaleFactor), int(18 * self.scaleFactor)), QColor("#999")))
        self.remove_from_favourites_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(20, 20, 20, .5);
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba(20, 20, 20, .9);
            }}
        """)

        self.button_center_layout = QHBoxLayout()
        self.button_center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_center_layout.addWidget(self.add_to_favourites_button)
        self.button_center_layout.addWidget(self.remove_from_favourites_button)

        self.loading_label = QLabel("Processing...")
        self.loading_label.setStyleSheet(f"font-size: {int(12 * self.scaleFactor)}px; padding-left: {int(5 * self.scaleFactor)}px; padding-right: {int(5 * self.scaleFactor)}px; border-radius: 5px; background-color: rgba(20, 20, 20, .5); color: #999;")
        self.loading_label.setVisible(False)
        self.button_center_layout.addWidget(self.loading_label)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.emoji)
        self.layout.addWidget(self.preview_button)
        self.layout.addLayout(self.button_center_layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(250)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self.hide_preview)

    def hide_preview(self):
        self.setVisible(False)

    def close_preview(self):
        self.fade_out_anim.start()

    def remove_from_favourites(self):
        if not self.sticker_favourites_name or not self.sticker_pack_name or not self.sticker_original_name:
            return

        r = request_helpers.make_request(
            f"{SERVER}/api/stickers/favourites",
            method="POST",
            json_data={"sticker_id": self.sticker_original_name.split("_")[0]}
        )
        self.remove_from_favourites_button.setVisible(False)
        self.add_to_favourites_button.setVisible(False)
        self.loading_label.setVisible(True)
        def req_finished():
            self.loading_label.setVisible(False)
            if r.error() == r.NetworkError.NoError:
                os.remove(os.path.join("stickers", "favourites", self.sticker_favourites_name))
                self.remove_from_favourites_button.setVisible(False)
                self.add_to_favourites_button.setVisible(True)
                if self.body_widget.current_pack == "favourites":
                    self.body_widget.load_favourites()
            r.deleteLater()
        r.finished.connect(req_finished)

    def add_to_favourites(self):
        if not self.sticker_favourites_name or not self.sticker_pack_name or not self.sticker_original_name:
            return
        r = request_helpers.make_request(
            f"{SERVER}/api/stickers/favourites",
            method="POST",
            json_data={"sticker_id": self.sticker_original_name.split("_")[0]}
        )
        self.remove_from_favourites_button.setVisible(False)
        self.add_to_favourites_button.setVisible(False)
        self.loading_label.setVisible(True)
        def req_finished():
            self.loading_label.setVisible(False)
            if r.error() == r.NetworkError.NoError:
                shutil.copy(os.path.join("stickers", self.sticker_pack_name, self.sticker_original_name),
                            os.path.join("stickers", "favourites", self.sticker_favourites_name))
                self.remove_from_favourites_button.setVisible(True)
                self.add_to_favourites_button.setVisible(False)
                if self.body_widget.current_pack == "favourites":
                    self.body_widget.load_favourites()
            r.deleteLater()
        r.finished.connect(req_finished)

    def show_preview(self, icon: QIcon, pack, sticker_name: str, start_pos=QPoint(0, 0)):
        sticker_id = sticker_name.split(".")[0].split("_")[0]
        sticker_emoji = sticker_name.split(".")[0].split("+")[1]
        sticker_extension = sticker_name.split(".")[-1]

        self.sticker_favourites_name = f"{sticker_id}_favourites+{sticker_emoji}.{sticker_extension}"
        if os.path.exists(os.path.join("stickers", "favourites", self.sticker_favourites_name)):
            self.remove_from_favourites_button.setVisible(True)
            self.add_to_favourites_button.setVisible(False)
        else:
            self.remove_from_favourites_button.setVisible(False)
            self.add_to_favourites_button.setVisible(True)

        if not self.current_user.logged_in:
            self.remove_from_favourites_button.setVisible(False)
            self.add_to_favourites_button.setVisible(False)

        self.sticker_original_name = sticker_name
        self.sticker_pack_name = pack

        try:
            self.preview_button.clicked.disconnect()
        except (RuntimeWarning, RuntimeError):
            pass
        self.preview_button.clicked.connect(lambda checked=False: self.body_widget.copy_sticker(pack, sticker_name))
        self.preview_button.setIcon(icon)
        self.emoji.setText(emoji.emojize(":" + sticker_name.split(".")[0].split("+")[1] + ":"))
        self.raise_()
        self.setVisible(True)
        self.fade_in_anim.start()
