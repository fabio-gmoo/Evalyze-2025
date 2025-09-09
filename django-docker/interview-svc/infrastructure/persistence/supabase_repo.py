from typing import Any
from supabase import create_client  # type: ignore
from application.ports.message_repo_port import MessageRepoPort
from infrastructure.config.settings import settings


class SupabaseMessageRepo(MessageRepoPort):
    def __init__(self) -> None:
        self.client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        self.table = settings.supabase_table

    def save(
        self, session_id: str, user_sub: str | None, payload: dict[str, Any]
    ) -> None:
        self.client.table(self.table).insert(
            {"session_id": session_id, "user_sub": user_sub, "payload": payload}
        ).execute()
