import time

import requests


class LLMClient:
    def __init__(self, model: str, api_key: str, fallback_model: str = ""):
        self.model = model
        self.fallback_model = fallback_model
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
        payload_template = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error: Exception | None = None
        for model_name in models_to_try:
            url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}"
            for attempt in range(3):
                try:
                    response = requests.post(
                        url,
                        json=payload_template,
                        timeout=30,
                    )
                    if response.status_code in (429, 500, 502, 503, 504):
                        # Retry các lỗi tạm thời từ nhà cung cấp model.
                        time.sleep(1 + attempt)
                        continue

                    response.raise_for_status()
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return ""
                    parts = candidates[0].get("content", {}).get("parts", [])
                    texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
                    answer = "\n".join([t for t in texts if t]).strip()
                    if answer:
                        return answer
                    return ""
                except requests.RequestException as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(1 + attempt)
                    continue

        if isinstance(last_error, requests.HTTPError) and last_error.response is not None:
            status_code = last_error.response.status_code
            if status_code == 503:
                raise RuntimeError(
                    "Gemini đang quá tải tạm thời (503). Vui lòng thử lại sau vài giây hoặc đổi GEMINI_MODEL."
                ) from last_error
            if status_code == 403:
                raise RuntimeError(
                    "Gemini từ chối truy cập (403). Kiểm tra lại GEMINI_API_KEY hoặc tạo key mới."
                ) from last_error

        raise RuntimeError(
            "Không gọi được Gemini API. Kiểm tra GEMINI_MODEL, GEMINI_API_KEY và kết nối mạng."
        ) from last_error
