import os

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import QRegion, QIcon, QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect, QVBoxLayout, QMainWindow, \
    QSystemTrayIcon

from modules import ui_helpers
from modules.ui_helpers import svg_to_icon

ICON_PATH = os.path.join("utils", "icon.png")


class Toast(QFrame):
    def __init__(self, text, timeout=3000, variant="info", parent=None):
        super().__init__(parent)
        self.timeout = timeout
        self.variant = variant

        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.scaleFactor = ui_helpers.get_screen_scale()

        self.setFixedWidth(int(200 * self.scaleFactor))

        self.setStyleSheet(f"""
            QFrame {{
                border-radius: 6px;
                font-size: {11 * self.scaleFactor}px;
                background-color: #333;
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        icon_files = {
            "info": {
                "icon": "info.svg",
                "color": "#999",
            },
            "warning": {
                "icon": "triangle-alert.svg",
                "color": "#FF7B00",
            },
            "error": {
                "icon": "circle-alert.svg",
                "color": "#DE0000",
            },
            "success": {
                "icon": "check.svg",
                "color": "#00A600",
            },
        }
        icon = QIcon(svg_to_icon(
            os.path.join("utils", "ui", icon_files[variant]["icon"]),
            QSize(int(16 * self.scaleFactor),
                  int(16 * self.scaleFactor)), QColor(icon_files[variant]["color"])))

        self.setLayout(main_layout)
        icon_widget = QLabel()
        icon_widget.setFixedSize(int(16 * self.scaleFactor), int(16 * self.scaleFactor))
        icon_widget.setPixmap(icon.pixmap(QSize(int(16 * self.scaleFactor), int(16 * self.scaleFactor))))
        main_layout.addWidget(icon_widget)

        text_layout = QVBoxLayout()

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(self.label.sizePolicy().horizontalPolicy(), self.label.sizePolicy().verticalPolicy())
        self.label.setMaximumWidth(int(200 * self.scaleFactor) - 40)
        self.label.adjustSize()
        text_layout.addWidget(self.label)

        self.hover_notice = QLabel("Hover to dismiss")
        self.hover_notice.setStyleSheet(f"font-size: {9 * self.scaleFactor}px")
        text_layout.addWidget(self.hover_notice)
        self.hover_notice.hide()

        main_layout.addLayout(text_layout)

        self.adjustSize()
        self.label.adjustSize()

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self._remove_self)

    def enterEvent(self, event):
        event.accept()
        self.fade_out_anim.start()

    def show_with_animation(self):
        self.adjustSize()
        self.label.adjustSize()
        self.fade_in_anim.start()
        if not self.timeout:
            self.hover_notice.show()
            return
        QTimer.singleShot(self.timeout, self.fade_out_anim.start)

    def _remove_self(self):
        self.setParent(None)
        self.deleteLater()


class QToastProvider(QFrame):
    def __init__(self, parent: QMainWindow, tray_icon: QSystemTrayIcon):
        super().__init__(parent)
        self.tray_icon = tray_icon
        self.setObjectName("toast_holder")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        self.setMouseTracking(True)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(5, 5, 20, 5)

        self.toasts = []

    def _update_mask(self):
        try:
            has_visible_toasts = False

            region = QRegion()
            for toast in self.toasts:
                if toast is None or not toast.isVisible():
                    continue
                has_visible_toasts = True
                r = toast.geometry()
                region = region.united(QRegion(r))

            self.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                not has_visible_toasts,
            )
            self.setMask(region)
        except RuntimeError:
            return

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._update_mask)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()

    def show_toast(self, text, timeout=3000, variant="info"):
        # noinspection PyTypeChecker
        parent_window: QMainWindow = self.parent()

        icon_variants = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
            "success": QSystemTrayIcon.MessageIcon.NoIcon,
        }

        if not parent_window.isVisible():
            self.tray_icon.showMessage(
                "Æther Desktop",
                text,
                icon_variants[variant],
                timeout,
            )

        toast = Toast(text, timeout, variant, parent=self)
        toast.adjustSize()

        margins = self.layout.contentsMargins()
        spacing = self.layout.spacing()

        current_height = sum(i.sizeHint().height() for i in self.toasts)
        if self.toasts:
            current_height += spacing * (len(self.toasts) - 1)

        available_height = self.parent().height() - margins.top() - margins.bottom()
        needed_height = current_height + (spacing if self.toasts else 0) + toast.sizeHint().height()

        while self.toasts and needed_height > available_height:
            last_toast = self.toasts.pop(0)
            self.layout.removeWidget(last_toast)
            last_toast.close()
            last_toast.deleteLater()

            current_height = sum(i.sizeHint().height() for i in self.toasts)
            if self.toasts:
                current_height += spacing * (len(self.toasts) - 1)
            needed_height = current_height + (spacing if self.toasts else 0) + toast.sizeHint().height()

        self.raise_()
        self.layout.addWidget(toast)
        self.toasts.append(toast)

        toast.show_with_animation()
        toast.destroyed.connect(lambda: self._cleanup(toast))

        QTimer.singleShot(0, self._update_mask)

    def _cleanup(self, toast):
        try:
            if toast in self.toasts:
                self.toasts.remove(toast)
            self._update_mask()
        except RuntimeError:
            return
