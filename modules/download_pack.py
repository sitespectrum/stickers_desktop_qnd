import json
import time

from PySide6.QtCore import QObject, Signal, QThread

from modules import request_helpers
from globals.constants import SERVER, DOWNLOAD_THREAD_LIMIT


def _chunk_list(lst, n_chunks=DOWNLOAD_THREAD_LIMIT):
    avg = len(lst) / float(n_chunks)
    chunks = []
    last = 0.0

    while last < len(lst):
        chunks.append(lst[int(last):int(last + avg)])
        last += avg

    return chunks


class _DownloadThread(QThread):
    finished = Signal()
    progress = Signal(int)

    def __init__(self, chunk: list):
        super().__init__()
        self.chunk = chunk

    def run(self):
        for file in self.chunk:
            self.progress.emit(1)
        self.finished.emit()


class DownloadPack(QObject):
    percent_changed = Signal(int)
    download_failed = Signal(str)
    pack_downloaded = Signal(str)

    def __init__(self):
        super().__init__()
        self._percent = 0
        self._reply = None
        self._threads = []
        self._finished_threads = 0
        self._total_items = 0
        self._processed_items = 0

    def download_pack(self, pack_name: str):
        self._percent = 0
        self._finished_threads = 0
        self._processed_items = 0
        self._total_items = 0
        self.percent_changed.emit(self._percent)

        def on_item_processed(count):
            self._processed_items += count
            percent = int(self._processed_items / self._total_items * 100)
            self.percent_changed.emit(percent)

        def on_thread_finished():
            self._finished_threads += 1
            if self._finished_threads == len(self._threads):
                self.pack_downloaded.emit(pack_name)
                print("Pack downloaded")

        def on_req_finished():
            if self._reply.error() == self._reply.NetworkError.NoError:
                # noinspection PyBroadException
                try:
                    data = bytes(self._reply.readAll())
                    body = json.loads(data.decode("utf-8")) if data else {}
                    self._total_items = len(body['stickers'])
                    chunks = _chunk_list(body['stickers'])
                    self._threads = [_DownloadThread(chunk) for chunk in chunks]
                    for thread in self._threads:
                        thread.progress.connect(on_item_processed)
                        thread.finished.connect(on_thread_finished)
                        thread.start()

                except Exception:
                    self.download_failed.emit("Unexpected error downloading pack")
                finally:
                    self._reply.deleteLater()
                    self._reply = None
            elif self._reply.error() == self._reply.NetworkError.ContentNotFoundError:
                self.download_failed.emit("Pack not found")
                self.percent_changed.emit(100)
            else:
                self.percent_changed.emit(100)
                self.download_failed.emit("Unexpected error downloading pack")

        self._reply = request_helpers.make_request(f"{SERVER}/api/stickers/get_pack/{pack_name}")
        self._reply.finished.connect(on_req_finished)
