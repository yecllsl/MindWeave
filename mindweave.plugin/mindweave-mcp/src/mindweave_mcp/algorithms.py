"""SM-2 间隔重复算法（移植 VocabCraft 已验证实现，语义一致）。

四级制 4/3/2/1；grade>=3 成功推进，grade<3 失败重置。
EF 无论对错都更新，下限 1.3。参考 SuperMemo 2 (1987)。
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _today_utc() -> date:
    return _now_utc().date()


def compute_next_review(ease_factor: float, interval: int, repetitions: int, grade: int) -> dict[str, Any]:
    if not 1 <= grade <= 4:
        raise ValueError(f"grade 必须在 1-4 之间，收到: {grade}")

    if grade < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)

    new_ease = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if new_ease < MIN_EASE_FACTOR:
        new_ease = MIN_EASE_FACTOR

    next_review_date = (_today_utc() + timedelta(days=new_interval)).isoformat()
    return {
        "ease_factor": new_ease,
        "interval": new_interval,
        "repetitions": new_repetitions,
        "next_review_date": next_review_date,
    }
