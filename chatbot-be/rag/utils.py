from __future__ import annotations
import re
from typing import List

def clean_text(t: str) -> str:
    t = t.replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> List[str]:
    """
    Простая нарезка по абзацам с overlap. Стабильно работает для PDF-выгрузки.
    """
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []
    buf = ""

    for p in paras:
        if len(buf) + len(p) + 1 <= max_chars:
            buf = (buf + "\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            # start new with overlap tail
            if overlap > 0 and chunks:
                tail = chunks[-1][-overlap:]
                buf = (tail + "\n" + p).strip()
            else:
                buf = p

    if buf:
        chunks.append(buf)

    # 필터: 너무 짧은 조각 제거
    chunks = [c for c in chunks if len(c) >= 120]
    return chunks
