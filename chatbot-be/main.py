# main.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.gemini_answer import render_answer_with_gemini

from rag.retriever import retrieve_evidence
from rag.prompt_ko import (
    SYSTEM_TLDR,
    smart_extract_ko,
    detect_intent_ko,
    build_answer_ko,
)

app = FastAPI(title="NutriGuard Backend", version="1.0.0")

# CORS (개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMsg(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMsg] = Field(default_factory=list)


class Evidence(BaseModel):
    source: str = ""
    snippet: str = ""
    score: Optional[float] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    intent: str
    parsed: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)


@app.get("/health")
def health():
    return {
        "ok": True,
        "ragEnabled": True,
        "rules": "ko_only",
        "hasSystemTLDR": bool(SYSTEM_TLDR),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    user_msg = (req.message or "").strip()
    history = req.history or []

    # 1) Smart extract (regex): 혈당/시간/상황 등
    parsed = smart_extract_ko(user_msg)

    # 2) Intent
    intent = detect_intent_ko(user_msg, parsed=parsed)

    # 3) Retrieval query (⚠️ SYSTEM_TLDR를 검색에 넣지 말기)
    #    user message + 아주 짧은 intent 힌트 + (있으면) 파싱된 신호만
    q_parts = [user_msg, f"[의도:{intent}]"]
    if parsed.get("timing"):
        q_parts.append(f"[시점:{parsed['timing']}]")
    if parsed.get("glucose_mgdl") is not None:
        q_parts.append(f"[혈당:{parsed['glucose_mgdl']}mg/dL]")
    retrieval_query = " ".join(q_parts)

    raw = retrieve_evidence(query=retrieval_query, k=int(os.getenv("RAG_K", "6")))

    # 4) Evidence 정리: 중복/너무 긴 텍스트 정리
    evidence: List[Dict[str, Any]] = []
    seen_keys = set()
    for r in raw:
        meta = r.get("meta") or {}
        key = (r.get("source", ""), meta.get("qid", meta.get("id", "")), meta.get("tags_str", ""))
        if key in seen_keys:
            continue
        seen_keys.add(key)

        snippet = (r.get("snippet") or "").strip()
        if len(snippet) > 320:
            snippet = snippet[:320].rstrip() + "…"

        evidence.append(
            {
                "source": r.get("source", ""),
                "snippet": snippet,
                "score": r.get("score"),
                "meta": meta,
            }
        )

        # UI 과밀 방지
        if len(evidence) >= 3:
            break

    # 5) Answer build (ko-only rules + anti-repeat tips)
    use_gemini = os.getenv("USE_GEMINI", "false").lower() == "true"

    if use_gemini:
        try:
            answer = render_answer_with_gemini(
                user_msg=user_msg,
                intent=intent,
                parsed=parsed,
                evidence=evidence,
                history=[m.model_dump() for m in history],
            )
        except Exception:
            answer = build_answer_ko(
            user_msg=user_msg,
            intent=intent,
            evidence=evidence,
            history=[m.model_dump() for m in history],
            parsed=parsed,
        )
    else:
        answer = build_answer_ko(
        user_msg=user_msg,
        intent=intent,
        evidence=evidence,
        history=[m.model_dump() for m in history],
        parsed=parsed,
    )

    return {
        "answer": answer,
        "intent": intent,
        "parsed": parsed,
        "evidence": evidence,
    }