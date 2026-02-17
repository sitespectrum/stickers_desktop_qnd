from collections import OrderedDict

from PySide6.QtGui import QIcon


class StickerIconCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = OrderedDict()

    def add_icon(self, key, icon: QIcon):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = icon

    def get_icon(self, key):
        icon = self.cache.get(key)
        if icon:
            self.cache.move_to_end(key)
            return icon
        else:
            new_icon = QIcon(key)
            self.add_icon(key, new_icon)
            return new_icon
    def __contains__(self, key):
        return key in self.cache
