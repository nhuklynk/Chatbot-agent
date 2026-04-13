import requests


class LLMClient:
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
        lines: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lines.append(f"[HE_THONG]\n{content}\n")
            elif role == "assistant":
                lines.append(f"[TRO_LY]\n{content}\n")
            else:
                lines.append(f"[NGUOI_DUNG]\n{content}\n")
        return "\n".join(lines).strip()

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            return (
                "Hệ thống đang chạy chế độ fallback vì chưa có API key (GEMINI_API_KEY). "
                "Hãy thêm API key để có câu trả lời thông minh hơn."
            )

        prompt = self._messages_to_prompt(messages)
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
        return "\n".join([t for t in texts if t]).strip()
