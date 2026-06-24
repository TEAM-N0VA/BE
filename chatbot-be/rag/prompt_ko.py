# rag/prompt_ko.py
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# --- SYSTEM RULES (LLM 없어도 "스타일 가이드"로 사용) ---
SYSTEM_TLDR = """
- 너는 임신성 당뇨(GDM) FAQ 도우미다.
- 출력은 반드시 한국어로만 한다. (영어/러시아어 금지)
- 의료진을 대체하지 않는다. 위험 신호/심하면 진료 권고.
- 답변은 짧고 실용적으로: 한줄요약 → 행동 2~3개 → 주의 → 근거요약 → 추가질문(1개)
- 같은 질문이 반복되면 표현/팁을 바꿔서 반복을 줄인다.
""".strip()

# --- Smart extractor (regex) ---
# 목표: "식후 1시간 145" 같은 문장 → timing, glucose(mg/dL), 상황 플래그 추출

_RE_GLUCOSE = re.compile(
    r"(?:혈당|BS|BG)?\s*[:=]?\s*(\d{2,3})\s*(?:mg\s*/\s*dL|mg/dl|mgdl)?",
    re.IGNORECASE,
)

# timing 패턴(띄어쓰기 변형 포함)
_RE_TIMING = [
    (re.compile(r"(공복|아침공복|기상\s*후)", re.IGNORECASE), "공복"),
    (re.compile(r"(식후)\s*(\d)\s*시간", re.IGNORECASE), None),  # 식후 N시간
    (re.compile(r"(식후)\s*(\d{1,2})\s*분", re.IGNORECASE), None),  # 식후 N분
    (re.compile(r"(취침\s*전|자기\s*전)", re.IGNORECASE), "취침 전"),
]

_RE_SITUATION_FLAGS = {
    "외식": re.compile(r"(외식|배달|식당|주문|메뉴|뷔페)", re.IGNORECASE),
    "간식": re.compile(r"(간식|빵|과자|디저트|아이스크림|초콜릿|케이크)", re.IGNORECASE),
    "운동": re.compile(r"(운동|산책|요가|헬스|필라테스)", re.IGNORECASE),
    "저혈당": re.compile(r"(저혈당|어지러|식은땀|손떨림|심장\s*두근|기절)", re.IGNORECASE),
    "측정": re.compile(r"(측정|재다|기록|기입|로그|혈당계|연속혈당|CGM)", re.IGNORECASE),
    "자세": re.compile(r"(눕|바로\s*눕|식후\s*눕|소화|속\s*더부룩)", re.IGNORECASE),
    "음료": re.compile(r"(카페|커피|라떼|주스|음료|탄산|제로|디카페인)", re.IGNORECASE),
}


def smart_extract_ko(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    t_nospace = re.sub(r"\s+", "", t)

    parsed: Dict[str, Any] = {
        "glucose_mgdl": None,
        "timing": None,           # 예: "식후1시간", "공복", "취침 전"
        "timing_minutes": None,   # 정규화(가능하면)
        "flags": [],              # 상황 태그
    }

    # glucose
    m = _RE_GLUCOSE.search(t)
    if m:
        try:
            val = int(m.group(1))
            # 현실 범위 필터(너무 엉뚱한 숫자 방지)
            if 40 <= val <= 350:
                parsed["glucose_mgdl"] = val
        except Exception:
            pass

    # timing
    for rx, label in _RE_TIMING:
        mm = rx.search(t)
        if not mm:
            continue
        if label:
            parsed["timing"] = label
            break
        # label None인 경우: 식후 N시간/분
        base = mm.group(1)  # "식후"
        num = mm.group(2)
        try:
            n = int(num)
            if "시간" in rx.pattern:
                parsed["timing"] = f"{base}{n}시간"
                parsed["timing_minutes"] = n * 60
            else:
                parsed["timing"] = f"{base}{n}분"
                parsed["timing_minutes"] = n
            break
        except Exception:
            continue

    # flags
    flags = []
    for k, rx in _RE_SITUATION_FLAGS.items():
        if rx.search(t) or rx.search(t_nospace):
            flags.append(k)
    parsed["flags"] = flags

    return parsed


# --- Intent detection ---
INTENTS = [
    "저혈당_대처",
    "혈당_해석_다음식사",
    "공복_혈당",
    "외식_주문",
    "간식_선택",
    "운동_전후_혈당",
    "측정_기록",
    "식후_자세_위장",
    "카페_음료",
    "일반_FAQ",
]


def detect_intent_ko(text: str, parsed: Optional[Dict[str, Any]] = None) -> str:
    t = (text or "").strip()
    t_ns = re.sub(r"\s+", "", t)
    parsed = parsed or {}
    flags = set(parsed.get("flags") or [])

    # 1) emergency-ish
    if "저혈당" in flags:
        return "저혈당_대처"

    # 2) measurement/logging
    if "측정" in flags:
        return "측정_기록"

    # 3) dining/snacks/drinks/exercise/posture
    if "외식" in flags:
        return "외식_주문"
    if "간식" in flags:
        return "간식_선택"
    if "운동" in flags:
        return "운동_전후_혈당"
    if "자세" in flags:
        return "식후_자세_위장"
    if "음료" in flags:
        return "카페_음료"

    # 4) glucose interpretation
    if parsed.get("glucose_mgdl") is not None:
        # 공복 / 식후가 같이 있으면 더 강하게
        if parsed.get("timing") in ("공복",) or "공복" in t_ns:
            return "공복_혈당"
        return "혈당_해석_다음식사"

    # 5) keyword fallback
    if any(k in t_ns for k in ["공복", "아침공복", "기상후"]):
        return "공복_혈당"
    if any(k in t_ns for k in ["식후", "1시간", "2시간", "혈당", "mgdl", "mg/dl"]):
        return "혈당_해석_다음식사"

    return "일반_FAQ"


# --- Tips pool (anti-repeat) ---
TIPS_POOL: Dict[str, List[List[str]]] = {
    "저혈당_대처": [
        ["즉시 15g 빠른 탄수화물(주스/사탕)을 섭취하세요.", "15분 후 재측정하고 필요하면 한 번 더 반복하세요.", "증상이 심하거나 의식저하가 있으면 바로 의료진/응급 도움을 받으세요."],
        ["앉아서 안정하고, 빠른 당(젤리/설탕물)을 먼저 드세요.", "회복 후에는 단백질/복합탄수로 유지(예: 우유 대신 두유/견과는 개인 상황에 맞게)하세요.", "저혈당이 잦으면 담당의와 약/식사 계획을 조정하세요."],
    ],
    "혈당_해석_다음식사": [
        ["다음 끼니는 정제 탄수(흰쌀/빵) 양을 줄이고 채소→단백질→탄수 순서로 드세요.", "가능하면 식후 10~15분 가볍게 걷기(무리 없이) 해보세요.", "같은 메뉴에서 반복 상승이면 탄수량/간식 타이밍을 조정하세요."],
        ["다음 식사는 탄수 비중을 낮추고(잡곡도 양 조절), 단백질·채소를 늘리세요.", "음료/디저트가 있었다면 다음엔 ‘무가당/제로’로 바꿔보세요.", "기록(시간/메뉴/수치)을 남기면 패턴 찾기 쉬워요."],
    ],
    "공복_혈당": [
        ["전날 저녁 탄수/야식이 많았다면 저녁 탄수를 조금 줄여보세요.", "취침 전 배고프면 소량 단백질 중심 간식을 고려하세요(개인 지시 우선).", "공복 수치가 지속적으로 높으면 의료진과 목표/계획을 점검하세요."],
        ["늦은 시간 간식(빵/과자/과일)을 피하고, 저녁은 단백질+채소 중심으로 구성하세요.", "수면 부족/스트레스도 공복에 영향이 있어요.", "며칠 기록 후 추세로 판단하세요."],
    ],
    "외식_주문": [
        ["밥/면은 ‘반 공기’ 요청, 단백질(고기/생선/두부)과 채소 반찬을 늘리세요.", "소스/양념은 따로, 달거나 걸쭉한 소스는 적게.", "식후 가벼운 걷기를 루틴으로."],
        ["국물/전/튀김/달달한 양념은 양을 줄이고, 구이·찜·샤브처럼 단순 조리 선택.", "음료는 물/무가당 차, 디저트는 가능한 패스.", "먹은 양을 대략 기록해두면 다음 선택이 쉬워요."],
    ],
    "간식_선택": [
        ["간식은 ‘단백질/지방 + 섬유’ 조합이 안정적이에요(예: 견과 소량 + 채소/무가당).", "빵/과자류는 양을 작게, 가능하면 식후에 소량으로.", "새 간식은 수치 반응을 보고 고정하세요."],
        ["당이 빠르게 오르는 간식(쿠키/케이크/과일주스)은 피하고, 무가당/저당 옵션을 선택하세요.", "간식 시간을 일정하게 두고 ‘배고픔 폭주’를 막아보세요.", "외출 시 대체 간식을 미리 준비하면 좋아요."],
    ],
    "운동_전후_혈당": [
        ["운동 전후로 혈당을 확인하고, 너무 낮으면 먼저 보충하세요.", "식후 10~30분 가벼운 걷기가 도움이 되는 경우가 많아요.", "무리한 강도는 피하고 꾸준함이 중요해요."],
        ["운동은 ‘짧게 자주’가 좋아요(예: 10분 걷기 x 2~3회).", "운동 후 어지럼/저혈당 증상이 있으면 즉시 대처하세요.", "운동 종류/시간대에 따라 반응이 달라서 기록 추천."],
    ],
    "측정_기록": [
        ["측정 시간(공복/식후 1~2시간)을 일정하게 맞추면 비교가 쉬워요.", "메뉴와 수치를 같이 기록하면 원인 파악이 빨라요.", "기기 오차가 있을 수 있어 손 씻기/채혈 방법도 점검하세요."],
        ["기록은 ‘시간-메뉴-수치-컨디션(수면/스트레스)’ 4가지만 적어도 충분해요.", "반복 상승 메뉴를 2~3개만 먼저 찾아 조정해보세요.", "지속적으로 목표 초과면 의료진 상담이 우선이에요."],
    ],
    "식후_자세_위장": [
        ["식후 바로 눕기보다는 10~15분 가볍게 움직여보세요.", "속이 더부룩하면 한 번에 많이 먹기보다 나눠 먹기가 좋아요.", "역류/통증이 심하면 진료 권고."],
        ["식후 눕는 습관은 혈당/소화에 불리할 수 있어요.", "물은 조금씩, 탄산/달달한 음료는 피하세요.", "증상이 지속되면 담당의와 상담하세요."],
    ],
    "카페_음료": [
        ["라떼/주스 대신 아메리카노(무가당)나 무가당 차를 선택하세요.", "시럽/휘핑은 빼고, ‘제로’도 개인 반응을 확인하세요.", "카페인은 개인 상태에 따라 제한이 필요할 수 있어요."],
        ["음료는 ‘무가당’이 기본이에요.", "당이 들어간 음료는 혈당을 빠르게 올릴 수 있어요.", "새 음료는 소량으로 반응을 확인하세요."],
    ],
    "일반_FAQ": [
        ["질문 상황(공복/식후 몇 시간, 수치, 먹은 것)을 알려주면 더 정확히 도와드릴게요.", "가능하면 최근 1~2회 기록을 함께 적어주세요.", "증상이 심하거나 불안하면 의료진 상담이 우선이에요."],
        ["현재가 공복인지 식후인지, 수치가 몇인지 알려주면 다음 행동을 구체화할 수 있어요.", "한 번에 하나씩 바꾸고(탄수량/간식/운동) 반응을 확인하세요.", "긴급 증상(실신/심한 어지럼)은 즉시 도움 요청."],
    ],
}

# 간단한 금지/안전 문구
SAFETY_NOTE = "※ 증상이 심하거나 수치가 계속 목표를 초과하면 담당 의료진 상담이 우선이에요."


def _flatten_history_text(history: List[Dict[str, Any]]) -> str:
    # 최근 assistant 응답들만 대충 합쳐서 anti-repeat 체크
    texts = []
    for m in history[-6:]:
        if (m.get("role") or "") == "assistant":
            texts.append(m.get("content") or "")
    return "\n".join(texts)


def _pick_tips(intent: str, history: List[Dict[str, Any]]) -> List[str]:
    pool = TIPS_POOL.get(intent) or TIPS_POOL["일반_FAQ"]
    prev = _flatten_history_text(history)
    # 이전 답변에 문장들이 많이 포함된 세트는 피함
    best = pool[0]
    best_overlap = 10**9
    for cand in pool:
        overlap = sum(1 for s in cand if s and s in prev)
        if overlap < best_overlap:
            best_overlap = overlap
            best = cand
    return best


def _evidence_summary(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        return "📌 근거: 관련 FAQ를 직접 매칭하지 못했어요. (시점/수치/메뉴를 더 알려주면 정확도가 올라가요.)"

    # 질문/답변 텍스트가 너무 길면 정리해서 1~2개만 보여주기
    lines = []
    for e in evidence[:2]:
        meta = e.get("meta") or {}
        qid = meta.get("qid") or meta.get("id") or ""
        src = e.get("source") or "FAQ"
        snip = (e.get("snippet") or "").strip()

        # "질문: ...\n답변: ..." 형태면 답변만 우선 보여주기
        if "답변:" in snip:
            snip = snip.split("답변:", 1)[-1].strip()
        snip = snip.replace("\n", " ").strip()
        if len(snip) > 160:
            snip = snip[:160].rstrip() + "…"

        head = f"- {snip}"
        lines.append(head)

    return "💡 더 궁금한다면^^:\n" + "\n".join(lines)


def _one_followup_question(intent: str, parsed: Dict[str, Any]) -> str:
    # intent + parsed 기준으로 딱 1개 질문
    if intent in ("혈당_해석_다음식사", "공복_혈당"):
        if parsed.get("glucose_mgdl") is None:
            return "혈당 수치가 몇 mg/dL인지 알려주실래요?"
        if not parsed.get("timing"):
            return "공복인지, 식후 몇 시간 수치인지 알려주실래요?"
        return "방금 드신 식사/간식(탄수 종류와 양)을 간단히 적어주실래요?"
    if intent == "외식_주문":
        return "어느 음식점/메뉴를 생각 중이신가요?"
    if intent == "간식_선택":
        return "지금 간식이 필요한 시간대(공복/식후)와 선호하는 음식이 있나요?"
    if intent == "운동_전후_혈당":
        return "운동은 식사 후 몇 분/몇 시간 뒤에 하실 계획인가요?"
    if intent == "저혈당_대처":
        return "현재 증상이 있고 혈당을 측정할 수 있는 상태인가요?"
    return "현재 공복/식후 시점과 최근 수치를 알려주실래요?"


def build_answer_ko(
    user_msg: str,
    intent: str,
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
    parsed: Optional[Dict[str, Any]] = None,
) -> str:
    parsed = parsed or {}
    tips = _pick_tips(intent, history)

    glucose = parsed.get("glucose_mgdl")
    timing = parsed.get("timing")

    # 한 줄 요약 (깔끔하게)
    if intent == "혈당_해석_다음식사" and glucose is not None and timing:
        headline = f"✅ 요약: {timing} {glucose}mg/dL → 다음 끼니는 탄수 조절 + 가벼운 활동이 핵심이에요."
    elif intent == "공복_혈당" and glucose is not None:
        headline = f"✅ 요약: 공복 {glucose}mg/dL → 저녁/수면/간식 패턴을 점검해요."
    elif intent == "저혈당_대처":
        headline = "✅ 요약: 저혈당 의심이면 ‘빠른 당 → 재측정’이 우선이에요."
    elif intent == "외식_주문":
        headline = "✅ 요약: 외식은 ‘탄수 양 줄이기 + 단백질/채소 늘리기’가 기본이에요."
    elif intent == "간식_선택":
        headline = "✅ 요약: 간식은 ‘빠른 당’보다 ‘단백질/섬유 조합’이 안정적이에요."
    else:
        headline = "✅ 요약: 시점(공복/식후) + 수치 + 메뉴를 알면 더 정확해요."

    # 행동 3개 (표기 깔끔)
    actions = "🧭 지금 할 일:\n" + "\n".join([f"- {tips[0]}", f"- {tips[1]}", f"- {tips[2]}"])

    # 주의 (너무 딱딱한 라벨 제거)
    caution_lines = []
    if glucose is not None:
        if glucose >= 200:
            caution_lines.append("수치가 많이 높아요. 반복되면 의료진 상담이 필요해요.")
        elif glucose <= 60:
            caution_lines.append("저혈당 범위일 수 있어요. 즉시 대처가 필요해요.")
    if not caution_lines:
        caution_lines.append(SAFETY_NOTE.replace("※ ", ""))

    caution = "⚠️ 주의:\n" + "\n".join([f"- {x}" for x in caution_lines])

    # 근거 요약 (더 궁금.. 부분)
    ev_text = _evidence_summary(evidence)

    # 추가 질문 1개
    follow = _one_followup_question(intent, parsed)

    return "\n\n".join([
        headline,
        actions,
        caution,
        ev_text,
        f"❓ 추가 질문: {follow}",
    ])

    # 최종 조립
    body = [
        headline,
        "",
        "행동(2~3개):",
        f"- {tips[0]}",
        f"- {tips[1]}",
        f"- {tips[2]}",
        "",
        caution,
        "",
        ev_text,
        "",
        f"추가 질문(1개): {follow}",
    ]
    return "\n".join(body)