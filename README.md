# Chatbot AI Agent (FastAPI)

Project nay tao mot AI Agent co:
- **Workflow ro rang**: chat + memory + retrieval context.
- **Prompt hoan chinh**: he thong prompt rieng de dieu huong chat.
- **Kha nang nap tai lieu linh hoat**: ingest URL, text, hoac file de dung lam ngu canh tra loi.
- **Chuan hoa du lieu dau vao**: dung `kreuzberg` de trich xuat va lam sach text.
- **API de demo nhanh**: phu hop cho buoi bao cao ky thuat.

## 1) Yeu cau

- Python 3.10+ (khuyen nghi 3.11)
- Co Internet neu can ingest URL hoac goi LLM
- Neu ingest `doc/docx`, nen cai them `pandoc` trong may de trich xuat on dinh hon

## 2) Cai dat

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Sua `.env` de dung Gemini:

```env
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
```

Ghi chu:
- He thong chi dung Gemini, khong con phan cau hinh OpenAI/provider.
- Neu khong co key, he thong van chay fallback mode de demo workflow.

## 3) Chay server

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Mo Swagger de test nhanh:
- [http://localhost:8000/docs](http://localhost:8000/docs)

Mo UI web:
- [http://localhost:8000](http://localhost:8000)
- Giao dien co 2 khu: upload du lieu va chat
- Lich su chat tren UI duoc luu localStorage nen F5 khong mat ngay

## 4) Quy trinh demo de thi

### Buoc A - Nap tai lieu
Goi API `POST /ingest-url`:

```json
{
  "url": "https://vi.wikipedia.org/wiki/Tr%C3%AD_tu%E1%BB%87_nh%C3%A2n_t%E1%BA%A1o"
}
```

Hoac nap text truc tiep bang `POST /ingest-text`:

```json
{
  "source": "ghi-chu-nhom-1",
  "text": "Noi dung tai lieu cua toi..."
}
```

Hoac upload file bang `POST /ingest-file`:
- Form-data key: `file`
- Ho tro: `.txt`, `.md`, `.csv`, `.json`, `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`
- File upload duoc chuan hoa qua `kreuzberg` truoc khi dua vao knowledge base
- Knowledge base duoc luu xuong `data/knowledge_base.json` de giu du lieu qua restart server

### Buoc B - Chat voi agent
Goi API `POST /chat`:

```json
{
  "session_id": "team-a",
  "message": "Tom tat 3 y chinh tu tai lieu vua nap"
}
```

### Ket qua
- `source = knowledge_base`: cau tra loi co su dung tai lieu ingest.
- `source = general`: cau tra loi tong quat.

## 5) Kien truc nhanh

- `backend/app/main.py`: FastAPI endpoints
- `backend/app/workflow.py`: logic dieu phoi agent
- `backend/app/tools.py`: lay text tu URL + chunking
- `backend/app/retriever.py`: tim context lien quan (TF-IDF)
- `backend/app/memory.py`: nho lich su hoi dap theo `session_id`
- `prompts/system_prompt.md`: prompt he thong

## 6) Goi y trinh bay voi BGK

- Nhan manh agent co day du: **logic + prompt + workflow + kha nang chay that**.
- Demo 1 URL tai lieu bat ky, hoi cau co lien quan, cho thay ket qua co context.
- Giai thich fallback mode khi khong co API key (de tranh vo demo).
