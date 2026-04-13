from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-2.5-flash-lite"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
