import json
from pathlib import Path


def save_knowledge_base(file_path: Path, docs: list[str], sources: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    items = [{"text": doc, "source": source} for doc, source in zip(docs, sources)]
    payload = {"items": items}
    file_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_knowledge_base(file_path: Path) -> list[dict[str, str]]:
    if not file_path.exists():
        return []
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    items = payload.get("items", [])
    valid_items = []
    for item in items:
        text = str(item.get("text", "")).strip()
        source = str(item.get("source", "unknown")).strip() or "unknown"
        if text:
            valid_items.append({"text": text, "source": source})
    return valid_items
