"""数据模型：康奈尔笔记 + 知识卡(cue) + SM-2 状态 + 复习记录。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]


class ReviewState(BaseModel):
    """卡级 SM-2 记忆状态。新卡初始：reps=0 / EF=2.5 / interval=0 / next_review=次日。"""
    repetitions: int = Field(default=0)
    ease_factor: float = Field(default=2.5)
    interval: int = Field(default=0)
    next_review: str = Field(default="", description="YYYY-MM-DD，空串=未排程")


class Cue(BaseModel):
    """知识卡 = 线索栏一行。"""
    cue_id: str = Field(description="{note_id}_c{NN}")
    question: str = Field(description="正面：线索问题")
    answer_hint: str = Field(default="", description="背面锚点")
    review_state: ReviewState = Field(default_factory=ReviewState)

    @field_validator("cue_id")
    @classmethod
    def _validate_cue_id(cls, v: str) -> str:
        # 格式 {note_id}_c{NN}：note_ 前缀 + _c 分隔符（计划测试 test_cue_id_prefix_validated
        # 要求 bad_c1 被拒——仅检查 "_c" 会漏过，须同时校验 note_ 前缀）
        if not (v.startswith("note_") and "_c" in v):
            raise ValueError(f"cue_id 须为 {{note_id}}_c{{NN}} 格式，收到: {v}")
        return v


class Cornell(BaseModel):
    body: str = Field(default="", description="笔记栏（markdown）")
    summary: str = Field(default="", description="总结栏")
    # 必填 + min_length=1：模型层硬兜底 spec §7 #4「cues 至少 1 条」。
    # 注意：不可写 default_factory=list —— Pydantic v2 默认 validate_default=False，
    # 默认值（含 default_factory 产物 []）会跳过 min_length 校验，兜底形同虚设（评审 B4）。
    # 工具层（save/update）仍保留友好 {error} 校验为第一道防线
    cues: list[Cue] = Field(min_length=1, description="线索栏（>=1 条，必填）")


class NoteRecord(BaseModel):
    note_id: str = Field(description="note_YYYYMMDD_NNN")
    created_at: str = Field(description="ISO")
    updated_at: str = Field(description="ISO")
    subject: str = Field(description="K12 九学科枚举")
    knowledge_points: list[str] = Field(default_factory=list)
    cornell: Cornell
    source: dict[str, Any] = Field(default_factory=dict, description="{image_path?, raw_text?}")

    @field_validator("note_id")
    @classmethod
    def _validate_note_id(cls, v: str) -> str:
        if not v.startswith("note_"):
            raise ValueError(f"note_id 须以 'note_' 开头，收到: {v}")
        return v

    @field_validator("subject")
    @classmethod
    def _validate_subject(cls, v: str) -> str:
        if v not in SUBJECTS:
            raise ValueError(f"subject 必须是 {SUBJECTS} 之一，收到: {v}")
        return v


class ReviewRecord(BaseModel):
    record_id: str
    note_id: str
    cue_id: str
    review_time: str = Field(description="ISO")
    grade: int = Field(description="1-4")

    @field_validator("grade")
    @classmethod
    def _validate_grade(cls, v: int) -> int:
        if not 1 <= v <= 4:
            raise ValueError(f"grade 必须在 1-4 之间，收到: {v}")
        return v
