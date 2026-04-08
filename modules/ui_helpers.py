from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QIcon, QPixmap, Qt, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from globals.settings import settings


def svg_to_icon(svg_path: str, size: QSize, tint: QColor | None = None) -> QIcon:
    renderer = QSvgRenderer(str(svg_path))
    pm = QPixmap(size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    renderer.render(p)

    if tint is not None:
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(pm.rect(), tint)

    p.end()
    return QIcon(pm)


def get_screen_scale():
    if not settings.screen_scale:
        return QApplication.primaryScreen().devicePixelRatio()
    return settings.screen_scale
