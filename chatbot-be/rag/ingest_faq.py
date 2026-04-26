# rag/ingest_faq.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer

# --- Stable paths (macOS uvicorn cwd-safe) ---
BACKEND_ROOT = Path(__file__).resolve().parent.parent  # .../backend
CHROMA_PATH = str(Path(os.getenv("CHROMA_PATH", BACKEND_ROOT / ".chroma")))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "faq_ko_gdm")
FAQ_PATH = os.getenv("FAQ_PATH", str(BACKEND_ROOT / "knowledge" / "faq" / "faq.jsonl"))

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

BATCH = int(os.getenv("INGEST_BATCH", "64"))


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"faq.jsonl not found: {p}")
    items: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _make_doc(item: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str]:
    """
    Return (doc_text, metadata, id)
    doc_text는 retrieval에 최적: 질문+답변 중심, 태그/출처는 메타로
    """
    qid = str(item.get("id") or item.get("qid") or "")
    q = (item.get("question") or "").strip()
    a = (item.get("answer") or "").strip()
    tags = item.get("tags") or []
    source = str(item.get("source") or "curated_faq")

    # doc 텍스트는 "질문/답변" 중심 (UI snippet도 깔끔)
    doc = f"질문: {q}\n답변: {a}".strip()

    tags = item.get("tags")

    if isinstance(tags, list):
        tags = ",".join(tags)

    meta = {
        "tags_str": tags,
    }
    #meta = {
        #"qid": qid,
        #"source": source,
        #"tags": tags,
        #"tags_str": ",".join(tags) if isinstance(tags, list) else str(tags),
        #"question": q,
   # }

    # Chroma id는 반드시 고유
    if not qid:
        # fallback: stable-ish hash
        qid = f"faq_{abs(hash(q + '|' + a))}"
    return doc, meta, qid


def ingest():
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col = client.get_or_create_collection(name=COLLECTION_NAME)

    items = _load_jsonl(FAQ_PATH)
    if not items:
        print("[WARN] faq.jsonl is empty")
        return

    model = SentenceTransformer(EMBED_MODEL)

    docs: List[str] = []
    metas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for it in items:
        doc, meta, qid = _make_doc(it)
        docs.append(doc)
        metas.append(meta)
        ids.append(qid)

    # batch upsert
    total = len(docs)
    for i in range(0, total, BATCH):
        j = min(i + BATCH, total)
        batch_docs = docs[i:j]
        batch_metas = metas[i:j]
        batch_ids = ids[i:j]

        embs = model.encode(batch_docs, normalize_embeddings=True).tolist()
        col.upsert(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=embs,
        )
        print(f"[INGEST] {j}/{total}")

    print(f"[DONE] indexed {total} items into collection='{COLLECTION_NAME}' at '{CHROMA_PATH}'")


if __name__ == "__main__":
    ingest()