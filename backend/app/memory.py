from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class Turn:
    role: str
    content: str


class SessionMemory:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self._store: dict[str, deque[Turn]] = defaultdict(
            lambda: deque(maxlen=self.max_turns * 2)
        )

    def add_user_message(self, session_id: str, message: str) -> None:
        self._store[session_id].append(Turn(role="user", content=message))

    def add_assistant_message(self, session_id: str, message: str) -> None:
        self._store[session_id].append(Turn(role="assistant", content=message))

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        turns = self._store.get(session_id, deque())
        return [{"role": t.role, "content": t.content} for t in turns]
