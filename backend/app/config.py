from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    system_prompt_path: str = "prompts/system_prompt.md"
    max_turns_memory: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def load_system_prompt(self, project_root: Path) -> str:
        prompt_file = project_root / self.system_prompt_path
        if not prompt_file.exists():
            return (
                "Bạn là trợ lý AI tiếng Việt. "
                "Trả lời rõ ràng, đúng trọng tâm, và nếu không chắc chắn thì nói rõ."
            )
        return prompt_file.read_text(encoding="utf-8").strip()

    def get_llm_provider(self) -> str:
        return (self.llm_provider or "openai").strip().lower()

    def get_llm_api_key(self) -> str:
        if self.llm_api_key:
            return self.llm_api_key
        if self.get_llm_provider() == "gemini":
            return self.gemini_api_key
        return self.openai_api_key

    def get_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        if self.get_llm_provider() == "gemini":
            return self.gemini_model
        return self.openai_model

    def get_llm_base_url(self) -> str:
        if self.llm_base_url:
            return self.llm_base_url
        if self.get_llm_provider() == "gemini":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
