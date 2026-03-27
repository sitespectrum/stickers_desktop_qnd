import json
import os
import time
import uuid
from json import JSONDecodeError

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGraphicsBlurEffect, \
    QGraphicsOpacityEffect, QWidget, QHBoxLayout

from globals.constants import SERVER
from modules import request_helpers

from globals.user import user
from modules.ui_helpers import svg_to_icon
from widgets import toast
from widgets.note import edit_note, confirm_delete_note


def _clear_layout(layout=None):
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()


class Body(QFrame):
    def __init__(self, edit_note_widget: edit_note.EditNote, confirm_delete_widget: confirm_delete_note.ConfirmDeleteNote, toast_provider: toast.QToastProvider, parent=None):
        super().__init__(parent)
        self.setObjectName("body")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.current_user = user
        self.current_user.logged_inChanged.connect(self.get_notes)

        self.primary_screen = QGuiApplication.primaryScreen()
        self.scaleFactor = self.primary_screen.devicePixelRatio()

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.toast_provider = toast_provider

        self.note_open = False

        self.edit_note = edit_note_widget
        self.edit_note.close_button.clicked.connect(self.close_note)
        self.edit_note.save_button.clicked.connect(self.save_note)
        self.edit_note.delete_button.clicked.connect(self.delete_note)

        self.confirm_delete_widget = confirm_delete_widget
        self.confirm_delete_widget.confirm_button.clicked.connect(lambda: self.delete_note(confirmed=True))
        self.confirm_delete_widget.cancel_button.clicked.connect(self.edit_note.show)

        self.scroll_layout = QVBoxLayout(self.scroll_area)
        self.scroll_layout.setContentsMargins(0, 0, int(5 * self.scaleFactor), int(40 * self.scaleFactor))
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)

        self.bottom_bar = QWidget(parent=self)
        self.bottom_bar.setObjectName("bottom_bar")
        self.bottom_bar.setFixedHeight(int(32 * self.scaleFactor))
        self.bottom_bar.setStyleSheet(
            "#bottom_bar {border-radius: 5px; background-color: #191919; border: 1px solid #333;}")
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(int(6 * self.scaleFactor), 0, int(6 * self.scaleFactor), 0)
        self.bottom_layout.setSpacing(int(6 * self.scaleFactor))

        self.add_note_button = QPushButton("Add Note")
        self.add_note_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "plus.svg"), QSize(int(20 * self.scaleFactor), int(20 * self.scaleFactor)), QColor("#999")))
        self.add_note_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_note_button.setFixedHeight(int(20 * self.scaleFactor))
        self.add_note_button.setFixedWidth(int(100 * self.scaleFactor))
        self.add_note_button.clicked.connect(self.add_note)
        self.bottom_layout.addWidget(self.add_note_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(svg_to_icon(os.path.join("utils", "ui", "refresh.svg"), QSize(int(20 * self.scaleFactor), int(20 * self.scaleFactor)), QColor("#999")))
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setFixedHeight(int(20 * self.scaleFactor))
        self.refresh_button.setFixedWidth(int(60 * self.scaleFactor))
        self.refresh_button.clicked.connect(self.get_notes)
        self.bottom_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.bottom_bar.setFixedWidth(self.bottom_layout.sizeHint().width())

        self.getting_ready_label = QLabel("Please wait for a moment while we prepare the application...")
        self.getting_ready_label.setWordWrap(True)
        self.getting_ready_label.setStyleSheet(f"font-size: {14 * self.scaleFactor}px")
        self.scroll_layout.addWidget(self.getting_ready_label)

        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                width: 5px;
                background: transparent;
            }
    
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 2px;
            }
    
            QScrollBar::handle:vertical:hover {
                background: #444;
            }
    
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
    
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
    
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #000;
                border-radius: 2px;
            }
            QScrollArea QWidget {
                background-color: transparent;
            }
        """)

        self.setStyleSheet("""
           #body {
               background-color: transparent;
           }
        """)

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

        self.overlay = QWidget(self)
        self.overlay.setFixedSize(self.size())
        self.overlay.setObjectName("overlay")
        self.overlay.setStyleSheet("background-color: rgba(33, 33, 33, .5);")

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.overlay.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        self.overlay.hide()

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

    def add_note(self):
        self.open_note()
        self.edit_note.delete_button.hide()
        self.edit_note.title.setText("")
        self.edit_note.content.setPlainText("")
        self.edit_note.note_id = 0

    def close_note(self):
        self.note_open = False
        self.blur_out_effect.start()
        self.fade_out_anim.start()
        self.edit_note.hide()

    def open_note(self):
        self.edit_note.end_loading()
        self.edit_note.delete_button.show()
        self.note_open = True
        self.blur_in_effect.start()
        self.overlay.show()
        self.fade_in_anim.start()
        self.overlay.show()
        self.overlay.raise_()
        self.edit_note.show()
        self.edit_note.raise_()

    def delete_note(self, confirmed=False):
        if self.edit_note.note_id is None:
            return
        if not confirmed:
            self.edit_note.hide()
            self.confirm_delete_widget.show()
            self.confirm_delete_widget.raise_()
            return
        self.edit_note.show()
        self.edit_note.loading()
        if self.current_user.logged_in:
            r = request_helpers.make_request(f"{SERVER}/api/notes/delete/{self.edit_note.note_id}", "DELETE")
            def req_finished():
                self.edit_note.end_loading()
                if r.error() == r.NetworkError.NoError:
                    self.close_note()
                    self.toast_provider.show_toast("Note deleted successfully.", variant="success")
                    self.get_notes()
                else:
                    try:
                        data = bytes(r.readAll())
                        body = json.loads(data.decode("utf-8")) if data else {}
                        error = body.get("error", "")
                        if error:
                            self.toast_provider.show_toast(error, variant="error")
                            return
                    except JSONDecodeError:
                        self.toast_provider.show_toast("Failed to delete note.", variant="error")
            r.finished.connect(req_finished)
        else:
            if not os.path.exists(os.path.join("data", "notes.json")):
                self.toast_provider.show_toast("Notes file not found", variant="error")
            with open(os.path.join("data", "notes.json"), "r") as f:
                notes = json.loads(f.read())
            notes.pop(self.edit_note.note_id, None)
            with open(os.path.join("data", "notes.json"), "w") as f:
                f.write(json.dumps(notes, indent=4))
            self.close_note()
            self.toast_provider.show_toast("Note deleted successfully.", variant="success")
            self.get_notes()

    def save_note(self):
        if self.edit_note.note_id is None:
            return
        elif not self.edit_note.content.toPlainText():
            self.toast_provider.show_toast("Note content cannot be empty.", variant="warning")
            return
        self.edit_note.loading()
        if self.current_user.logged_in:
            r = request_helpers.make_request(f"{SERVER}/api/notes/save/{self.edit_note.note_id}", "PUT", json_data={
                "name": self.edit_note.title.text(),
                "content": self.edit_note.content.toPlainText()
            })
            def req_finished():
                self.edit_note.end_loading()
                if r.error() == r.NetworkError.NoError:
                    self.close_note()
                    self.get_notes()
                    self.toast_provider.show_toast("Note saved successfully.", variant="success")
                else:
                    try:
                        data = bytes(r.readAll())
                        body = json.loads(data.decode("utf-8")) if data else {}
                        error = body.get("error", "")
                        if error:
                            self.toast_provider.show_toast(error, variant="error")
                            return
                    except JSONDecodeError:
                        self.toast_provider.show_toast("Failed to save note.", variant="error")
                r.deleteLater()
            r.finished.connect(req_finished)
        else:
            if not os.path.exists(os.path.join("data", "notes.json")):
                self.toast_provider.show_toast("Notes file not found", variant="error")
            with open(os.path.join("data", "notes.json"), "r") as f:
                notes = json.loads(f.read())
            if self.edit_note.note_id == 0:
                notes[str(uuid.uuid4())] = {
                    "name": self.edit_note.title.text(),
                    "content": self.edit_note.content.toPlainText()
                }
            else:
                note = notes.get(self.edit_note.note_id, None)
                if not note:
                    self.toast_provider.show_toast("Note not found", variant="error")
                    return
                note["name"] = self.edit_note.title.text()
                note["content"] = self.edit_note.content.toPlainText()
            with open(os.path.join("data", "notes.json"), "w") as f:
                f.write(json.dumps(notes, indent=4))
            self.close_note()
            self.toast_provider.show_toast("Note saved successfully.", variant="success")
            self.get_notes()

    def get_note_details(self, note_id: str):
        self.open_note()
        self.edit_note.loading()
        if self.current_user.logged_in:
            r = request_helpers.make_request(f"{SERVER}/api/notes/get/{note_id}")
            def req_finished():
                if r.error() == r.NetworkError.NoError:
                    note = json.loads(bytes(r.readAll()))["note"]
                    self.edit_note.title.setText(note["name"])
                    self.edit_note.content.setPlainText(note["content"])
                    self.edit_note.note_id = note_id
                    self.edit_note.end_loading()
                r.deleteLater()
            r.finished.connect(req_finished)
        else:
            if not os.path.exists(os.path.join("data", "notes.json")):
                self.toast_provider.show_toast("Notes file not found", variant="error")
            with open(os.path.join("data", "notes.json"), "r") as f:
                notes = json.loads(f.read())
            note = notes.get(note_id, {})
            if not note:
                self.toast_provider.show_toast("Note not found", variant="error")
                return
            self.edit_note.title.setText(note["name"])
            self.edit_note.content.setPlainText(note["content"])
            self.edit_note.note_id = note_id
            self.edit_note.end_loading()

    def get_notes(self):
        _clear_layout(self.scroll_layout)
        if self.current_user.logged_in:
            label = QLabel("Fetching notes...")
            label.setStyleSheet(f"color: #999; font-size: {int(12 * self.scaleFactor)}px")
            self.scroll_layout.addWidget(label)
            r = request_helpers.make_request(f"{SERVER}/api/notes/all")
            def req_finished():
                _clear_layout(self.scroll_layout)
                if r.error() == r.NetworkError.NoError:
                    notes = json.loads(bytes(r.readAll()))
                    if not notes["notes"]:
                        label = QLabel("No notes")
                        label.setStyleSheet(f"color: #999; font-size: {int(12 * self.scaleFactor)}px")
                        self.scroll_layout.addWidget(label)
                        return
                    for i in notes["notes"]:
                        button = QPushButton(i["name"].replace("\n", " "))
                        button.setCursor(Qt.CursorShape.PointingHandCursor)
                        button.setStyleSheet(f"""
                            QPushButton {{
                                background-color: #111;
                                border: none;
                                border-radius: 5px;
                                color: white;
                                font-size: {int(12 * self.scaleFactor)}px;
                                text-align: left;
                                padding: 5px;
                            }}
                            QPushButton:hover {{
                                background-color: #333;
                            }}
                            QPushButton:pressed {{
                                background-color: #444; 
                            }}
                        """)
                        self.scroll_layout.addWidget(button)
                        button.clicked.connect(lambda checked=False, note_id=i["id"]: self.get_note_details(note_id))
                r.deleteLater()
            r.finished.connect(req_finished)
        else:
            if not os.path.exists(os.path.join("data", "notes.json")):
                if not os.path.exists("data"):
                    os.mkdir("data")
                with open(os.path.join("data", "notes.json"), "w") as f:
                    f.write("{}")
            with open(os.path.join("data", "notes.json"), "r") as f:
                notes = json.loads(f.read())
            for i in notes.keys():
                button = QPushButton(notes[i]["name"].replace("\n", " "))
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #111;
                        border: none;
                        border-radius: 5px;
                        color: white;
                        font-size: {int(12 * self.scaleFactor)}px;
                        text-align: left;
                        padding: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: #333;
                    }}
                    QPushButton:pressed {{
                        background-color: #444; 
                    }}
                """)
                self.scroll_layout.addWidget(button)
                button.clicked.connect(lambda checked=False, note_id=i: self.get_note_details(note_id))
            if not notes:
                label = QLabel("No local notes")
                label.setStyleSheet(f"color: #999; font-size: {int(12 * self.scaleFactor)}px")
                self.scroll_layout.addWidget(label)

    def align_to_center(self, child=None,):
        child = child
        x = (self.width() - child.width()) // 2
        y = (self.height() - child.height()) // 2
        child.move(x, y)

    def resizeEvent(self, event):
        self.align_to_center(self.edit_note)
        self.align_to_center(self.confirm_delete_widget)

        self.bottom_bar.move(int(10 * self.scaleFactor), self.height() - self.bottom_bar.height() - int(10 * self.scaleFactor))
