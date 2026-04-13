import re
import tempfile
from pathlib import Path

from kreuzberg import ExtractionConfig, extract_bytes_sync, extract_file_sync


class InputNormalizer:
    def __init__(self):
        self._config = ExtractionConfig(
            enable_quality_processing=True,
            output_format="plain",
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = text.replace("\x00", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def normalize_text(self, text: str) -> str:
        if not text.strip():
            return ""
        result = extract_bytes_sync(
            text.encode("utf-8"),
            mime_type="text/plain",
            config=self._config,
        )
        content = result.content or ""
        return self._clean_text(content)

    def normalize_file(self, file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(file_bytes)

        try:
            result = extract_file_sync(temp_path, config=self._config)
            content = result.content or ""
            return self._clean_text(content)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
