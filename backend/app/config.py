from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-2.5-flash-lite"
    system_prompt_path: str = "prompts/system_prompt.md"
    max_turns_memory: int = 6
    storage_provider: str = "local"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_object_key: str = "knowledge_base.json"
    r2_endpoint_url: str = ""
    r2_region: str = "auto"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def load_system_prompt(self, project_root: Path) -> str:
        prompt_file = project_root / self.system_prompt_path
        if not prompt_file.exists():
            return (
                "Bạn là trợ lý AI tiếng Việt. "
                "Trả lời rõ ràng, đúng trọng tâm, và nếu không chắc chắn thì nói rõ."
            )
        return prompt_file.read_text(encoding="utf-8").strip()

    def get_r2_config(self) -> dict[str, str] | None:
        if self.storage_provider.strip().lower() != "r2":
            return None

        missing_fields = []
        if not self.r2_access_key_id.strip():
            missing_fields.append("R2_ACCESS_KEY_ID")
        if not self.r2_secret_access_key.strip():
            missing_fields.append("R2_SECRET_ACCESS_KEY")
        if not self.r2_bucket.strip():
            missing_fields.append("R2_BUCKET")

        endpoint = self.r2_endpoint_url.strip()
        if not endpoint:
            if not self.r2_account_id.strip():
                missing_fields.append("R2_ACCOUNT_ID hoặc R2_ENDPOINT_URL")
            else:
                endpoint = f"https://{self.r2_account_id.strip()}.r2.cloudflarestorage.com"

        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Thiếu cấu hình Cloudflare R2: {fields}")

        return {
            "endpoint_url": endpoint,
            "access_key_id": self.r2_access_key_id.strip(),
            "secret_access_key": self.r2_secret_access_key.strip(),
            "bucket": self.r2_bucket.strip(),
            "object_key": self.r2_object_key.strip() or "knowledge_base.json",
            "region": self.r2_region.strip() or "auto",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
