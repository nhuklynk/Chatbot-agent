from typing import Optional

from openai import OpenAI


class LLMClient:
    def __init__(self, provider: str, model: str, api_key: str, base_url: str = ""):
        self.provider = (provider or "openai").lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client: Optional[OpenAI] = None
        if api_key:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)

    def is_enabled(self) -> bool:
        return self.client is not None

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.client:
            provider_hint = "GEMINI_API_KEY" if self.provider == "gemini" else "OPENAI_API_KEY"
            return (
                f"He thong dang chay che do fallback vi chua co API key ({provider_hint}). "
                "Hay them API key de co cau tra loi thong minh hon."
            )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
