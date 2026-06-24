# rag/retriever.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

# --- Stable paths (macOS uvicorn cwd-safe) ---
BACKEND_ROOT = Path(__file__).resolve().parent.parent  # .../backend
CHROMA_PATH = str(Path(os.getenv("CHROMA_PATH", BACKEND_ROOT / ".chroma")))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "faq_ko_gdm")
EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

# Lazy singletons
_model: Optional[SentenceTransformer] = None
_client: Optional[chromadb.PersistentClient] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def _get_collection():
    client = _get_client()
    # collection이 없을 수도 있으니 get_or_create
    return client.get_or_create_collection(name=COLLECTION_NAME)


def retrieve_evidence(query: str, k: int = 3) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []

    model = _get_model()
    col = _get_collection()

    q_emb = model.encode([q], normalize_embeddings=True).tolist()[0]

    res = col.query(
        query_embeddings=[q_emb],
        n_results=max(1, int(k)),
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        source = str(meta.get("source", "curated_faq"))

        # chroma distance: 작을수록 유사. score는 보기 편하게 1/(1+dist)
        score = None
        try:
            score = float(1.0 / (1.0 + float(dist)))
        except Exception:
            score = None

        snippet = (doc or "").strip()
        out.append(
            {
                "source": source,
                "snippet": snippet,
                "score": score,
                "meta": meta,
            }
        )
    return out