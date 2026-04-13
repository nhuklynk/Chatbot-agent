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

    def _model_candidates(self) -> list[str]:
        preferred = [
            self.model,
            self.fallback_model,
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]
        seen: set[str] = set()
        ordered: list[str] = []
        for name in preferred:
            normalized = (name or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

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
        models_to_try = self._model_candidates()

        last_error: Exception | None = None
        last_failed_model = ""
        unavailable_models: list[str] = []
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
                    last_failed_model = model_name
                    if isinstance(exc, requests.HTTPError) and exc.response is not None:
                        # Model không tồn tại thì thử model khác luôn, không retry.
                        if exc.response.status_code == 404:
                            unavailable_models.append(model_name)
                            break
                    if attempt < 2:
                        time.sleep(1 + attempt)
                    continue

        if unavailable_models and len(unavailable_models) == len(models_to_try):
            model_list = ", ".join(f"`{name}`" for name in unavailable_models)
            raise RuntimeError(
                f"Các model Gemini đã thử đều không khả dụng: {model_list}. "
                "Hãy đặt `GEMINI_MODEL=gemini-2.5-flash` (hoặc `gemini-2.5-flash-lite`) rồi thử lại."
            ) from last_error

        if isinstance(last_error, requests.Timeout):
            raise RuntimeError(
                "Gọi Gemini bị quá thời gian chờ (timeout). Vui lòng thử lại hoặc kiểm tra kết nối mạng."
            ) from last_error

        if isinstance(last_error, requests.ConnectionError):
            raise RuntimeError(
                "Không kết nối được đến Gemini API. Kiểm tra mạng hoặc tường lửa/proxy của môi trường chạy."
            ) from last_error

        if isinstance(last_error, requests.HTTPError) and last_error.response is not None:
            status_code = last_error.response.status_code
            error_message = ""
            try:
                error_payload = last_error.response.json()
                if isinstance(error_payload, dict):
                    nested_error = error_payload.get("error")
                    if isinstance(nested_error, dict):
                        error_message = str(nested_error.get("message") or "")
                    elif "message" in error_payload:
                        error_message = str(error_payload.get("message") or "")
            except ValueError:
                error_message = (last_error.response.text or "").strip()

            if status_code == 503:
                raise RuntimeError(
                    "Gemini đang quá tải tạm thời (503). Vui lòng thử lại sau vài giây hoặc đổi GEMINI_MODEL."
                ) from last_error
            if status_code == 400:
                lowered_error = error_message.lower()
                if "api key expired" in lowered_error or "api_key_invalid" in lowered_error:
                    raise RuntimeError(
                        "GEMINI_API_KEY đã hết hạn hoặc không hợp lệ. Hãy tạo API key mới trong Google AI Studio và cập nhật lại `.env`."
                    ) from last_error
                raise RuntimeError(
                    f"Yêu cầu Gemini không hợp lệ (400): {error_message or 'Kiểm tra payload/model/API key.'}"
                ) from last_error
            if status_code == 403:
                raise RuntimeError(
                    "Gemini từ chối truy cập (403). Kiểm tra lại GEMINI_API_KEY hoặc tạo key mới."
                ) from last_error
            if status_code == 404:
                failed_model = last_failed_model or self.model
                raise RuntimeError(
                    f"Model Gemini không tồn tại/không khả dụng: `{failed_model}`. "
                    "Hãy đổi sang `gemini-2.5-flash` hoặc `gemini-2.5-flash-lite`."
                ) from last_error
            if status_code == 429:
                raise RuntimeError(
                    "Gemini đang giới hạn tần suất (429). Vui lòng đợi một lúc rồi thử lại."
                ) from last_error
            if error_message:
                raise RuntimeError(
                    f"Lỗi Gemini API (HTTP {status_code}): {error_message}"
                ) from last_error
            raise RuntimeError(
                f"Lỗi Gemini API (HTTP {status_code})."
            ) from last_error

        raise RuntimeError(
            "Không gọi được Gemini API. Kiểm tra GEMINI_MODEL, GEMINI_API_KEY và kết nối mạng."
        ) from last_error
