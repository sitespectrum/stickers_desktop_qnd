import json
from json import JSONDecodeError
from pathlib import Path

from PySide6.QtCore import QUrl, QByteArray
from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager

COOKIES_PATH = Path("cookies.json")


def get_status_code(reply):
    status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
    status_code = int(status) if status is not None else None
    return status_code


def get_cookies() -> dict:
    if not COOKIES_PATH.exists():
        return {}
    try:
        return json.loads(COOKIES_PATH.read_text(encoding="utf-8")) or {}
    except JSONDecodeError:
        return {}


def save_cookies(cookies: dict) -> None:
    COOKIES_PATH.write_text(json.dumps(cookies or {}, indent=2), encoding="utf-8")


def _cookies_dict_to_header_value(cookies: dict) -> str:
    if not cookies:
        return ""
    parts = []
    for k, v in cookies.items():
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return "; ".join(parts)


def _update_cookie_dict_from_set_cookie_headers(cookies: dict, set_cookie_headers: list[str]) -> dict:
    cookies = dict(cookies or {})
    for header in set_cookie_headers:
        if not header:
            continue
        first = header.split(";", 1)[0].strip()
        if "=" not in first:
            continue
        name, value = first.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name:
            cookies[name] = value
    return cookies


def persist_cookies_from_reply(reply, *, cookies: dict | None = None) -> dict:
    base = cookies if cookies is not None else get_cookies()

    set_cookie_headers: list[str] = []
    for k_ba, v_ba in reply.rawHeaderPairs():
        if bytes(k_ba).lower() == b"set-cookie":
            set_cookie_headers.append(bytes(v_ba).decode("utf-8", errors="replace"))

    updated = _update_cookie_dict_from_set_cookie_headers(base, set_cookie_headers)
    if updated != base:
        save_cookies(updated)
    return updated


def attach_cookie_persistence(reply, *, cookies: dict | None = None) -> None:

    def _on_finished():
        # noinspection PyBroadException
        try:
            persist_cookies_from_reply(reply, cookies=cookies)
        except Exception:
            pass

    reply.finished.connect(_on_finished)


_net = QNetworkAccessManager()


def make_request(
    url: str,
    method: str = "GET",
    *,
    net: QNetworkAccessManager = _net,
    headers: dict[str, str] | None = None,
    data: bytes | bytearray | QByteArray | None = None,
    json_data: dict | list | None = None,
    cookies: dict | None = None,
    persist_cookies: bool = True,
):
    method_u = (method or "GET").upper()
    req = QNetworkRequest(QUrl(url))

    if headers is None:
        headers = {"Accept": "application/json"}

    if headers:
        for k, v in headers.items():
            if v is None:
                continue
            req.setRawHeader(QByteArray(k.encode("utf-8")), QByteArray(str(v).encode("utf-8")))

    # Cookies
    if cookies is None:
        cookies = get_cookies()

    if cookies:
        cookie_header = _cookies_dict_to_header_value(cookies)
        if cookie_header:
            req.setRawHeader(b"Cookie", cookie_header.encode("utf-8"))

    # Body
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json; charset=utf-8")
        reply = net.sendCustomRequest(req, QByteArray(method_u.encode("utf-8")), QByteArray(body))
        if persist_cookies:
            attach_cookie_persistence(reply, cookies=cookies)
        return reply

    if data is None:
        if method_u == "GET":
            reply = net.get(req)
        elif method_u == "HEAD":
            reply = net.head(req)
        elif method_u == "DELETE":
            reply = net.deleteResource(req)
        else:
            reply = net.sendCustomRequest(req, QByteArray(method_u.encode("utf-8")))
        if persist_cookies:
            attach_cookie_persistence(reply, cookies=cookies)
        return reply

    body = data if isinstance(data, QByteArray) else QByteArray(bytes(data))

    if method_u == "POST":
        reply = net.post(req, body)
    elif method_u == "PUT":
        reply = net.put(req, body)
    else:
        reply = net.sendCustomRequest(req, QByteArray(method_u.encode("utf-8")), body)

    if persist_cookies:
        attach_cookie_persistence(reply, cookies=cookies)
    return reply
