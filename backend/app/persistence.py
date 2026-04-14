import json
from pathlib import Path


def _build_payload(docs: list[str], sources: list[str]) -> str:
    items = [{"text": doc, "source": source} for doc, source in zip(docs, sources)]
    payload = {"items": items}
    return json.dumps(payload, ensure_ascii=False)


def _create_r2_client(r2_config: dict[str, str]):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "Bạn đang dùng Cloudflare R2 nhưng chưa cài boto3. Hãy chạy: pip install boto3"
        ) from exc

    return boto3.client(
        "s3",
        endpoint_url=r2_config["endpoint_url"],
        aws_access_key_id=r2_config["access_key_id"],
        aws_secret_access_key=r2_config["secret_access_key"],
        region_name=r2_config["region"],
    )


def _save_to_r2(payload: str, r2_config: dict[str, str]) -> None:
    client = _create_r2_client(r2_config)
    client.put_object(
        Bucket=r2_config["bucket"],
        Key=r2_config["object_key"],
        Body=payload.encode("utf-8"),
        ContentType="application/json; charset=utf-8",
    )


def _load_from_r2(r2_config: dict[str, str]) -> str:
    client = _create_r2_client(r2_config)
    try:
        response = client.get_object(
            Bucket=r2_config["bucket"],
            Key=r2_config["object_key"],
        )
    except Exception as exc:
        code = ""
        if hasattr(exc, "response"):
            code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"NoSuchKey", "404", "NotFound"}:
            return ""
        raise
    body = response["Body"].read()
    return body.decode("utf-8") if body else ""


def save_knowledge_base(
    file_path: Path,
    docs: list[str],
    sources: list[str],
    r2_config: dict[str, str] | None = None,
) -> None:
    serialized_payload = _build_payload(docs, sources)
    if r2_config:
        _save_to_r2(serialized_payload, r2_config)
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(serialized_payload, encoding="utf-8")


def load_knowledge_base(
    file_path: Path,
    r2_config: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    if r2_config:
        raw_payload = _load_from_r2(r2_config)
        if not raw_payload:
            return []
    else:
        if not file_path.exists():
            return []
        raw_payload = file_path.read_text(encoding="utf-8")

    try:
        payload = json.loads(raw_payload)
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
