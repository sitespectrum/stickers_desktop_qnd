from PySide6.QtCore import QObject, Signal, Property
import os
import json


class Settings(QObject):
    changed = Signal(str, object)
    screen_scale_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._screen_scale = 0.0
        self._settings_object = {}
        if not os.path.exists("settings.json"):
            with open("settings.json", "w") as f:
                f.write(json.dumps({
                    "screen_scale": 0.0,
                }, indent=4))
        with open("settings.json", "r") as f:
            self._settings_object = json.loads(f.read())
            self._screen_scale = self._settings_object.get("screen_scale", 0.0)

    def save(self):
        with open("settings.json", "w") as f:
            f.write(json.dumps(self._settings_object, indent=4))

    # --- screen scale ---
    @Property(str, notify=screen_scale_changed)
    def screen_scale(self) -> float:
        return self._screen_scale

    # Requires restart
    @screen_scale.setter
    def screen_scale(self, value: float) -> None:
        value = value or 0.0
        if value == self._screen_scale:
            return
        self._settings_object["screen_scale"] = value
        self.save()
        print(f"Screen scale changed to {value}")
        self.screen_scale_changed.emit(self._screen_scale)
        self.changed.emit("screen_scale", self._screen_scale)


settings = Settings()
