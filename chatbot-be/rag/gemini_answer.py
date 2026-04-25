# rag/gemini_answer.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


def _make_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=GEMINI_API_KEY)


def _build_system_prompt() -> str:
    return """
너는 임신성 당뇨(GDM) FAQ 챗봇이다.

[절대 규칙]
- 반드시 한국어로만 답한다.
- 의료진을 대체하지 않는다.
- 제공된 user_message, intent, parsed, evidence만 바탕으로 답한다.
- 질문과 관련 없는 상황을 절대 섞지 않는다.
  예: 사용자가 식후 질문을 했는데 공복 예시를 넣지 않는다.
- evidence에 없는 새로운 의학적 사실을 만들어내지 않는다.
- 같은 내용을 반복하지 않는다.
- 내부 메타데이터를 절대 노출하지 않는다.
  예: faq_001, curated_faq, source, score, qid 같은 문자열 금지
- evidence 문장을 길게 복사하지 말고, 짧고 자연스럽게 재구성한다.
- 답변은 짧고 실용적이어야 한다.
- 사용자가 이미 말한 정보(예: 식후 1시간, 160, 떡볶이)를 적극 반영한다.

[답변 스타일]
- summary: 한 줄 핵심 요약
- actions: 지금 할 일 2~3개
- caution: 짧은 주의 1개
- followup: 추가 질문 1개
- advice는 선택 사항이 아니라, evidence를 바탕으로 한 "짧은 추천/조언" 1~2개만 쓴다.
- 장황한 설명 금지
- FAQ 원문 나열 금지
- 공손하고 자연스럽게, 하지만 짧게

[좋은 답변 예시]
사용자: "오늘 점심에 떡볶이 먹고 1시간 뒤 160 나왔어 뭐가 문제야?"
좋은 답변 방향:
- 떡볶이 같은 정제 탄수/양념 음식이 식후 혈당을 올릴 수 있다고 짧게 설명
- 다음 끼니 조절, 가벼운 걷기 제안
- 반복되면 상담 권고
- 마지막에 떡볶이 양/같이 먹은 음식 질문 1개

[나쁜 답변 예시]
- 공복 혈당 이야기 섞기
- 100mg/dL 예시, 110mg/dL 예시를 반복
- evidence를 길게 붙여넣기
- 내부 source/faq id 노출
""".strip()


def _clean_snippet(text: str) -> str:
    snip = (text or "").strip()

    if "답변:" in snip:
        snip = snip.split("답변:", 1)[-1].strip()

    snip = snip.replace("\n", " ").strip()

    # 내부 메타 제거용 간단 정리
    bad_tokens = [
        "curated_faq",
        "faq_",
        "source",
        "score",
        "qid",
        "질문:",
    ]
    for token in bad_tokens:
        snip = snip.replace(token, "")

    if len(snip) > 180:
        snip = snip[:180].rstrip() + "…"

    return snip


def _build_user_payload(
    user_msg: str,
    intent: str,
    parsed: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> str:
    # evidence는 1개만 우선 사용해서 관련 없는 내용 섞임 방지
    clean_evidence = []
    for e in evidence[:1]:
        clean_evidence.append(
            {
                "snippet": _clean_snippet(e.get("snippet") or ""),
            }
        )

    payload = {
        "user_message": user_msg,
        "intent": intent,
        "parsed": parsed,
        "history_tail": history[-4:],
        "evidence": clean_evidence,
        "response_style": {
            "tone": "친절하고 자연스럽지만 짧게",
            "sections": ["summary", "actions", "caution", "advice", "followup"],
            "max_actions": 3,
            "max_advice_items": 2,
            "avoid": [
                "공복/식후 혼동",
                "반복 문장",
                "내부 메타데이터 노출",
                "긴 FAQ 붙여넣기",
            ],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


_RESPONSE_SCHEMA = {
    "type": "object",
    "propertyOrdering": ["summary", "actions", "caution", "advice", "followup"],
    "properties": {
        "summary": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 3,
        },
        "caution": {"type": "string"},
        "advice": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2,
        },
        "followup": {"type": "string"},
    },
    "required": ["summary", "actions", "caution", "advice", "followup"],
    "additionalProperties": False,
}


def render_answer_with_gemini(
    user_msg: str,
    intent: str,
    parsed: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> str:
    client = _make_client()

    contents = _build_user_payload(
        user_msg=user_msg,
        intent=intent,
        parsed=parsed,
        evidence=evidence,
        history=history,
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=_build_system_prompt(),
            temperature=0.2,
            max_output_tokens=260,
            response_mime_type="application/json",
            response_json_schema=_RESPONSE_SCHEMA,
        ),
    )

    text = response.text or "{}"
    data = json.loads(text)

    summary = f"✅ 요약: {data['summary']}"
    actions = "🧭 지금 할 일:\n" + "\n".join(f"- {x}" for x in data["actions"])
    caution = f"⚠️ 주의:\n- {data['caution']}"
    advice = "💡 추천 · 조언:\n" + "\n".join(f"- {x}" for x in data["advice"])
    followup = f"❓ 추가 질문: {data['followup']}"

    return "\n\n".join([summary, actions, caution, advice, followup])