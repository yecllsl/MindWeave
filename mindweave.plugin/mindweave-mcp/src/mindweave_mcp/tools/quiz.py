"""AI 出题测验工具：generate_quiz（渲染命题 prompt + 占位落盘）/ save_quiz（校验回写）/ grade_quiz（判分推进 SM-2）。

设计（spec §2）：工具只渲染 prompt，真实命题/语义评分交宿主 LLM 执行；
save_quiz 经 QuizRecord 校验回写，禁止宿主直写 quizzes/ 文件（prompt 注入防线）。
仅对话链路使用，web 不调用。
"""
from __future__ import annotations

import unicodedata
from typing import Any

from pydantic import ValidationError

from mindweave_mcp.algorithms import _now_utc
from mindweave_mcp.models import NoteRecord, QuizRecord
from mindweave_mcp.prompts.quiz_generate_prompt import (
    FILL_GENERATE_PROMPT,
    SELECT_GENERATE_PROMPT,
)
from mindweave_mcp.prompts.quiz_grade_prompt import GRADE_PROMPT
from mindweave_mcp.tools.crud import ID_LOCK, _generate_id, get_storage
from mindweave_mcp.tools.review import apply_review

# 占位题干文本：generate 后未 save_quiz 回写的可见标记
_PLACEHOLDER_QUESTION = "（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）"


def _now_iso() -> str:
    return _now_utc().isoformat()


def _find_note_with_cue(storage: Any, cue_id: str) -> tuple[NoteRecord | None, Any]:
    """遍历笔记定位 cue 所在 note；未命中返回 (None, None)。"""
    for note in storage.get_all_notes():
        for cue in note.cornell.cues:
            if cue.cue_id == cue_id:
                return note, cue
    return None, None


def _generate_quiz_id(storage: Any) -> str:
    return _generate_id("quiz", storage.list_all_quiz_ids())


def generate_quiz(cue_id: str, quiz_type: str = "") -> dict[str, Any]:
    """为 cue 渲染命题 prompt，同时生成占位 Quiz 落盘（answer 空、question 占位）。

    宿主 LLM 按 generate_prompt 生成题干/选项/答案后，调 save_quiz 回写。

    Args:
        cue_id: 线索卡 ID
        quiz_type: 题型，仅两个**中文**枚举 "选择" / "填空"（写成 choice/fill 会被拒绝）；
            空串默认 "选择"
    """
    storage = get_storage()
    note, cue = _find_note_with_cue(storage, cue_id)
    if note is None:
        return {"error": f"cue 不存在: {cue_id}"}
    qtype = quiz_type or "选择"

    # 干扰项素材：同学科其他 cue 的线索问题（命题 prompt 用）
    distractor_pool = "\n".join(
        f"- {c.question}"
        for n in storage.get_all_notes() if n.subject == note.subject
        for c in n.cornell.cues if c.cue_id != cue_id
    ) or "（暂无同学科其他知识卡，请自行构造干扰项）"
    body_excerpt = note.cornell.body[:500]

    if qtype == "选择":
        prompt = SELECT_GENERATE_PROMPT.format(
            subject=note.subject, question=cue.question,
            answer_hint=cue.answer_hint, body_excerpt=body_excerpt,
            distractor_pool=distractor_pool,
        )
    elif qtype == "填空":
        prompt = FILL_GENERATE_PROMPT.format(
            subject=note.subject, question=cue.question,
            answer_hint=cue.answer_hint, body_excerpt=body_excerpt,
        )
    else:
        return {"error": f"quiz_type 须为 选择/填空，收到: {quiz_type}"}

    with ID_LOCK:
        quiz = QuizRecord(
            quiz_id=_generate_quiz_id(storage), note_id=note.note_id, cue_id=cue_id,
            quiz_type=qtype, question=_PLACEHOLDER_QUESTION, options=[], answer="",
            created_at=_now_iso(),
        )
        storage.save_quiz(quiz)
    return {
        "quiz_id": quiz.quiz_id, "quiz": quiz.model_dump(), "generate_prompt": prompt,
        "message": "请使用 generate_prompt 调用 LLM 生成题目，再调用 save_quiz 回写",
    }


def save_quiz(quiz_id: str, quiz_data: dict[str, Any]) -> dict[str, Any]:
    """宿主 LLM 生成的题干/选项/答案经 QuizRecord 校验后写回指定 quiz。

    服务端字段（quiz_id/note_id/cue_id/created_at/answered/grade）不可经 quiz_data 篡改。
    """
    storage = get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        return {"error": f"quiz 不存在: {quiz_id}"}
    # 必须走「重建 + model_validate」而非 model_copy(update=...)：Pydantic v2 的
    # model_copy 不触发校验，answer∈options / 4 选项等 validator 不会执行（安全防线失效）。
    # 重建合并 dict 后再整体验证，确保 answer∈options 硬防线真实生效（评审 A1 / spec P3-6）。
    try:
        merged = {**quiz.model_dump(), **{
            "question": str(quiz_data.get("question", quiz.question)),
            "options": [str(o) for o in quiz_data.get("options", []) or []],
            "answer": str(quiz_data.get("answer", quiz.answer)),
        }}
        updated = QuizRecord.model_validate(merged)
    except (ValidationError, ValueError, TypeError) as exc:
        return {"error": f"题目回写失败: {exc}"}
    storage.save_quiz(updated)
    return {"quiz_id": quiz_id, "saved": True}


def _normalize_answer(s: str) -> str:
    """判分归一化：NFKC（全角→半角、全角标点→ASCII）+ strip + lower（评审 P2-4）。"""
    return unicodedata.normalize("NFKC", s).strip().lower()


def grade_quiz(quiz_id: str, response: str) -> dict[str, Any]:
    """判分并按 SM-2 更新 cue 记忆状态（与 submit_review 等价推进）。

    判分口径（spec §2）：选择=客观题精确匹配（对→4/错→1，归一化后比较）；
    填空=语义题返回 grade_prompt 交宿主 LLM 评分，未回传默认 grade=3 推进。
    """
    storage = get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        return {"error": f"quiz 不存在: {quiz_id}"}
    # 硬防御①：空作答不是有效学习反馈，放行会以默认 grade 污染 SM-2
    if not (response or "").strip():
        return {"error": "作答为空，不允许评分", "quiz_id": quiz_id}
    # 硬防御②：占位题（answer 未回写）拒绝评分，防 ""=="" 得 grade=4
    if not quiz.answer.strip():
        return {"error": "该题答案为空（占位题尚未回写），不允许评分", "quiz_id": quiz_id}
    # 硬防御③：已判分 quiz 拒绝二次评分，防 SM-2 被二次推进
    if quiz.answered:
        return {"error": "该题已判分，不允许重复评分", "quiz_id": quiz_id}

    result: dict[str, Any] = {"quiz_id": quiz_id, "cue_id": quiz.cue_id}
    if quiz.quiz_type == "选择":
        correct = _normalize_answer(response) == _normalize_answer(quiz.answer)
        grade = 4 if correct else 1
        result["correct"] = correct
    else:  # 填空=语义题
        result["grade_prompt"] = GRADE_PROMPT.format(
            question=quiz.question, reference_answer=quiz.answer, user_answer=response,
        )
        result["correct"] = None
        # ponytail: 宿主 LLM 未回传语义评分时默认 grade=3 推进（VocabCraft 释义题同款降级）。
        # 已知取舍：对可能答错的语义题偏乐观；升级路径为「未回传不写 ReviewRecord、
        # 不推进 SM-2、仅提示重试」或新增回传工具。
        grade = 3
    result["grade"] = grade

    # 先推进 SM-2（apply_review 失败则 quiz 不标 answered，避免「已判分但记忆未推进」
    # 的死锁记录：若先 save answered=True 再 apply_review 失败，防御③会拒绝重判，评审 B1）。
    review_result = apply_review(quiz.cue_id, grade, source="quiz")
    if "error" in review_result:
        result["error"] = review_result["error"]
        return result

    # apply_review 成功后落盘判分状态。注：此处用 model_copy 而非重建校验，因为写入的
    # answered/grade 是服务端可信值（grade 已由判分防御保证 1-4），无需再触发 validator。
    storage.save_quiz(quiz.model_copy(update={"answered": True, "grade": grade}))

    result["next_review"] = review_result["next_review"]
    result["repetitions"] = review_result["repetitions"]
    result["ease_factor"] = review_result["ease_factor"]
    return result
