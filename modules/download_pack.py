import json
import os
import time

import emoji
from PySide6.QtCore import QObject, Signal, QThread, QEventLoop
from PySide6.QtNetwork import QNetworkRequest

from modules import request_helpers
from globals.constants import SERVER, DOWNLOAD_THREAD_LIMIT, CONTENT_TYPE_TO_EXT


def _chunk_list(lst, n_chunks=DOWNLOAD_THREAD_LIMIT):
    avg = len(lst) / float(n_chunks)
    chunks = []
    last = 0.0

    while last < len(lst):
        chunks.append(lst[int(last):int(last + avg)])
        last += avg

    return chunks


class _DownloadThread(QThread):
    thread_done = Signal()
    progress = Signal(int)

    def __init__(self, chunk: list, pack_name: str = ""):
        super().__init__()
        self.chunk = chunk
        self.request = None
        self.pack_name = pack_name

    def run(self):
        for file in self.chunk:
            sticker_id = file["id"]
            if file["is_video"] or file["is_animated"]:
                continue

            loop = QEventLoop()

            reply = request_helpers.make_request(
                f"{SERVER}/api/stickers/get_sticker/{sticker_id}"
            )

            reply.finished.connect(loop.quit)
            loop.exec()

            if reply.error() == reply.NetworkError.NoError:
                content_type = reply.header(QNetworkRequest.ContentTypeHeader)

                if isinstance(content_type, bytes):
                    content_type = content_type.decode()

                ext = CONTENT_TYPE_TO_EXT.get(content_type, ".bin")
                file_path = os.path.join("stickers", self.pack_name, f"{file["id"]}_{self.pack_name}+{emoji.demojize(file["emoji"]).replace(":", "")}{ext}")
                with open(file_path, "wb") as f:
                    f.write(bytes(reply.readAll()))

                self.progress.emit(1)

        self.thread_done.emit()


class _DownloadThumbnail(QThread):
    thread_done = Signal()
    progress = Signal(int)

    def __init__(self, thumbnail_id: str, pack_name: str):
        super().__init__()

        self.thumbnail_id = thumbnail_id
        self.request = None
        self.pack_name = pack_name

    def run(self):
        reply = request_helpers.make_request(
            f"{SERVER}/api/stickers/get_sticker/{self.thumbnail_id}"
        )

        loop = QEventLoop()

        reply.finished.connect(loop.quit)
        loop.exec()

        if reply.error() == reply.NetworkError.NoError:
            content_type = reply.header(QNetworkRequest.ContentTypeHeader)

            if isinstance(content_type, bytes):
                content_type = content_type.decode()

            ext = CONTENT_TYPE_TO_EXT.get(content_type, ".bin")
            file_path = os.path.join("stickers", self.pack_name,
                                     f"thumbnail{ext}")
            with open(file_path, "wb") as f:
                f.write(bytes(reply.readAll()))

            self.progress.emit(1)

        self.thread_done.emit()


class DownloadPack(QObject):
    percent_changed = Signal(int)
    download_failed = Signal(str)
    pack_downloaded = Signal(str)

    downloading = False

    def __init__(self):
        super().__init__()
        self._percent = 0
        self._reply = None
        self._threads: list[_DownloadThread | _DownloadThumbnail] = []
        self._finished_threads = 0
        self._total_items = 0
        self._processed_items = 0

    def download_pack(self, pack_name: str):
        self.downloading = True
        self._percent = 0
        self._finished_threads = 0
        self._processed_items = 0
        self._total_items = 0
        self.percent_changed.emit(self._percent)

        def on_item_processed(count: int):
            self._processed_items += count
            if self._total_items > 0:
                percent = int(self._processed_items / self._total_items * 100)
                self.percent_changed.emit(min(percent, 100))

        def on_thread_finished():
            self._finished_threads += 1
            if self._finished_threads == len(self._threads):
                self.downloading = False
                self.percent_changed.emit(100)
                self.pack_downloaded.emit(pack_name)

        def on_req_finished():
            if self._reply.error() == self._reply.NetworkError.NoError:
                # noinspection PyBroadException
                try:
                    data = bytes(self._reply.readAll())
                    body = json.loads(data.decode("utf-8")) if data else {}

                    stickers = body.get("stickers", [])
                    downloadable = [
                        s for s in stickers
                        if not s.get("is_video") and not s.get("is_animated")
                    ]

                    self._total_items = len(downloadable)
                    if self._total_items == 0:
                        self.downloading = False
                        self.percent_changed.emit(100)
                        self.pack_downloaded.emit(pack_name)
                        return

                    chunks = _chunk_list(downloadable)
                    self._threads = [_DownloadThread(chunk, pack_name) for chunk in chunks]
                    self._threads.append(_DownloadThumbnail(body.get("thumbnail"), pack_name))

                    for thread in self._threads:
                        thread.progress.connect(on_item_processed)
                        thread.thread_done.connect(on_thread_finished)
                        thread.start()

                except Exception:
                    self.downloading = False
                    self.download_failed.emit("Unexpected error downloading pack")
                finally:
                    self._reply.deleteLater()
                    self._reply = None

            elif self._reply.error() == self._reply.NetworkError.ContentNotFoundError:
                self.downloading = False
                self.download_failed.emit("Pack not found")
                self.percent_changed.emit(100)
            else:
                self.downloading = False
                self.percent_changed.emit(100)
                self.download_failed.emit("Unexpected error downloading pack")

        self._reply = request_helpers.make_request(f"{SERVER}/api/stickers/get_pack/{pack_name}")
        self.percent_changed.emit(0)
        self._reply.finished.connect(on_req_finished)
