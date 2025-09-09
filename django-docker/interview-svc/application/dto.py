from pydantic import BaseModel  # type: ignore


class ChatIn(BaseModel):
    session_id: str
    message: str
