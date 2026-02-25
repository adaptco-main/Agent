from typing import Any


class TestClient:
    __test__ = False
    def __init__(self, app):
        self.app = app

    def request(self, method: str, path: str, headers: dict[str, str] | None = None, json: Any = None):
        return self.app.handle(method, path, headers=headers, json_body=json)

    def get(self, path: str, headers: dict[str, str] | None = None):
        return self.request("GET", path, headers=headers)

    def post(self, path: str, headers: dict[str, str] | None = None, json: Any = None):
        return self.request("POST", path, headers=headers, json=json)
