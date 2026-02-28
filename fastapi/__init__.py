import asyncio
import inspect
import json
import re
from dataclasses import dataclass
from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass
class Depends:
    dependency: Callable[..., Any]


class URL:
    def __init__(self, path: str):
        self.path = path


class Request:
    def __init__(self, method: str, path: str, headers: dict[str, str] | None = None, body: bytes = b""):
        self.method = method.upper()
        self.url = URL(path)
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self._body = body

    async def body(self) -> bytes:
        return self._body


class Response:
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return self._data


class FastAPI:
    def __init__(self, title: str = ""):
        self.title = title
        self.routes: list[dict[str, Any]] = []

    def add_middleware(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def _add_route(self, method: str, path: str, func: Callable[..., Any], dependencies: list[Depends] | None = None):
        pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", path)
        self.routes.append(
            {
                "method": method.upper(),
                "path": path,
                "regex": re.compile(f"^{pattern}$"),
                "func": func,
                "dependencies": dependencies or [],
            }
        )

    def get(self, path: str, dependencies: list[Depends] | None = None):
        def decorator(func: Callable[..., Any]):
            self._add_route("GET", path, func, dependencies)
            return func

        return decorator

    def post(self, path: str, dependencies: list[Depends] | None = None):
        def decorator(func: Callable[..., Any]):
            self._add_route("POST", path, func, dependencies)
            return func

        return decorator

    def handle(self, method: str, path: str, headers: dict[str, str] | None = None, json_body: Any = None) -> Response:
        body = b"" if json_body is None else json.dumps(json_body).encode()
        request = Request(method, path, headers, body)
        for route in self.routes:
            if route["method"] != method.upper():
                continue
            match = route["regex"].match(path)
            if not match:
                continue
            try:
                for dep in route["dependencies"]:
                    self._call(dep.dependency, request)
                result = self._call(route["func"], request, **match.groupdict())
                return Response(200, result)
            except HTTPException as exc:
                return Response(exc.status_code, {"detail": exc.detail})
        return Response(404, {"detail": "Not found"})

    @staticmethod
    def _call(func: Callable[..., Any], request: Request, **path_params: Any) -> Any:
        sig = inspect.signature(func)
        kwargs = {}
        for name, param in sig.parameters.items():
            if name in path_params:
                kwargs[name] = path_params[name]
            elif param.annotation is Request or name == "request":
                kwargs[name] = request
        result = func(**kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result
