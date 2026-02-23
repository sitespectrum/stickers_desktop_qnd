import emoji
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QPushButton, QVBoxLayout, QLabel



class PreviewSticker(QFrame):
    def __init__(self,body_widget, parent=None):
        super().__init__(parent)

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

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.emoji)
        self.layout.addWidget(self.preview_button)
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

    def show_preview(self, icon: QIcon, pack, sticker_name: str, start_pos=QPoint(0, 0)):
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
