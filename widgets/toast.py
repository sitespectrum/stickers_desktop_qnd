from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QGuiApplication, QRegion
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect, QVBoxLayout, QBoxLayout


class Toast(QFrame):
    def __init__(self, text, timeout=3000, variant="info", parent=None):
        super().__init__(parent)
        self.timeout = timeout
        self.variant = variant

        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.setStyleSheet(self._variant_style())

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(text))

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

    def _variant_style(self):
        styles = {
            "info": """
                    background-color: rgb(40, 40, 40);
                """,
            "warning": """
                    background-color: #FF7B00;
                    color: black;
                """,
            "error": """
                    background-color: #590000;
                """,
            "success": """
                    background-color: #005400;
                """
        }

        style_data = styles.get(self.variant, styles["info"])

        return f"""
                QFrame {{
                    border-radius: 6px;
                    font-size: {9 * self.scaleFactor}px;
                    {style_data}
                }}
            """

    def show_with_animation(self):
        self.fade_in_anim.start()
        QTimer.singleShot(self.timeout, self.fade_out_anim.start)

    def _remove_self(self):
        self.setParent(None)
        self.deleteLater()


class QToastProvider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        if not self.toasts:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        region = QRegion()
        for toast in self.toasts:
            if toast is None or not toast.isVisible():
                continue
            r = toast.geometry()
            region = region.united(QRegion(r))
        self.setMask(region)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()

    def show_toast(self, text, timeout=3000, variant="info"):
        self.raise_()
        toast = Toast(text, timeout, variant, parent=self)

        self.layout.addWidget(toast)
        self.toasts.append(toast)

        toast.show_with_animation()

        toast.destroyed.connect(lambda: self._cleanup(toast))

        QTimer.singleShot(0, self._update_mask)

    def _cleanup(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
        self._update_mask()
