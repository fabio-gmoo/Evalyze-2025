from application.dto import ChatIn
from application.ports.ai_llm_port import AiLlmPort
from application.ports.message_repo_port import MessageRepoPort

SYSTEM_PROMPT = "Eres un entrevistador amable y profesional."


class ChatWithAi:
    def __init__(self, llm: AiLlmPort, repo: MessageRepoPort) -> None:
        self.llm = llm
        self.repo = repo

    def execute(self, input: ChatIn, user_sub: str | None) -> dict:
        # guardar pregunta del usuario
        self.repo.save(
            input.session_id, user_sub, {"role": "user", "content": input.message}
        )
        # pedir al LLM
        reply = self.llm.chat(SYSTEM_PROMPT, input.message)
        # guardar respuesta
        self.repo.save(
            input.session_id, user_sub, {"role": "assistant", "content": reply}
        )
        return {"reply": reply}
