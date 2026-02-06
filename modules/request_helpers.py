import json


def get_cookies():
    cookies = None
    with open('cookies.json', 'r') as f:
        cookies = json.loads(f.read())
    return cookies
