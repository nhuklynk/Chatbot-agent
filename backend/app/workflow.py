from dataclasses import dataclass

from .llm import LLMClient
from .memory import SessionMemory
from .retriever import InMemoryKnowledgeBase
from .tools import fetch_web_text, split_text_to_chunks


@dataclass
class AgentResult:
    answer: str
    source: str


class ChatbotAgent:
    def __init__(
        self,
        llm: LLMClient,
        memory: SessionMemory,
        kb: InMemoryKnowledgeBase,
        system_prompt: str,
    ):
        self.llm = llm
        self.memory = memory
        self.kb = kb
        self.system_prompt = system_prompt

    def ingest_url(self, url: str) -> int:
        text = fetch_web_text(url)
        chunks = split_text_to_chunks(text)
        self.kb.add_chunks(chunks=chunks, source=url)
        return len(chunks)

    def ingest_text(self, text: str, source: str = "manual_input") -> int:
        cleaned = text.strip()
        if not cleaned:
            return 0
        chunks = split_text_to_chunks(cleaned)
        self.kb.add_chunks(chunks=chunks, source=source)
        return len(chunks)

    def _build_messages(
        self, session_id: str, user_message: str, context_chunks: list[str]
    ) -> list[dict[str, str]]:
        context_text = "\n\n".join(
            [f"Context {idx + 1}: {chunk}" for idx, chunk in enumerate(context_chunks)]
        )
        system_content = self.system_prompt
        if context_text:
            system_content += (
                "\n\nSử dụng bối cảnh sau nếu liên quan. Nếu không đủ thông tin, nêu rõ hạn chế:\n"
                f"{context_text}"
            )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        messages.extend(self.memory.get_history(session_id))
        messages.append({"role": "user", "content": user_message})
        return messages

    def ask(self, session_id: str, user_message: str) -> AgentResult:
        self.memory.add_user_message(session_id, user_message)
        retrieved = self.kb.search(user_message, top_k=3)
        chunks = [item.text for item in retrieved]
        source = "knowledge_base" if retrieved else "general"

        messages = self._build_messages(session_id, user_message, chunks)
        answer = self.llm.chat(messages).strip()
        if not answer:
            answer = "Mình chưa tạo được câu trả lời phù hợp. Bạn thử đặt câu hỏi cụ thể hơn nhé."

        self.memory.add_assistant_message(session_id, answer)
        return AgentResult(answer=answer, source=source)
