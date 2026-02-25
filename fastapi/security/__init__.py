from dataclasses import dataclass


@dataclass
class HTTPAuthorizationCredentials:
    scheme: str
    credentials: str


class HTTPBearer:
    def __init__(self, auto_error: bool = False):
        self.auto_error = auto_error


def Security(value):
    return value
