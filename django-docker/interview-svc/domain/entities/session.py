from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    id: str
    user_sub: str | None
