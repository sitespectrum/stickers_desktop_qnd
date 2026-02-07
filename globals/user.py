from PySide6.QtCore import QObject, Signal, Property


class User(QObject):
    usernameChanged = Signal(str)
    displayNameChanged = Signal(str)
    roleChanged = Signal(str)
    logged_inChanged = Signal(bool)

    changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        self._display_name = ""
        self._role = ""
        self._logged_in = False

    # --- username ---
    @Property(str, notify=usernameChanged)
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        value = value or ""
        if value == self._username:
            return
        self._username = value
        self.usernameChanged.emit(self._username)
        self.changed.emit("username", self._username)

    # --- display_name ---
    @Property(str, notify=displayNameChanged)
    def display_name(self) -> str:
        return self._display_name

    @display_name.setter
    def display_name(self, value: str) -> None:
        value = value or ""
        if value == self._display_name:
            return
        self._display_name = value
        self.displayNameChanged.emit(self._display_name)
        self.changed.emit("display_name", self._display_name)

    # --- role ---
    @Property(str, notify=roleChanged)
    def role(self) -> str:
        return self._role

    @role.setter
    def role(self, value: str) -> None:
        value = value or ""
        if value == self._role:
            return
        self._role = value
        self.roleChanged.emit(self._role)
        self.changed.emit("role", self._role)

    # --- logged_in ---
    @Property(bool, notify=logged_inChanged)
    def logged_in(self) -> bool:
        return self._logged_in

    @logged_in.setter
    def logged_in(self, value: bool) -> None:
        self._logged_in = value
        self.logged_inChanged.emit(self._logged_in)
        self.changed.emit("logged_in", self._logged_in)


user = User()
