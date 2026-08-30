"""康奈尔整理提示词（三模式：对话多模态 > 本地路径多模态 > 文本）。"""
from __future__ import annotations

SUBJECTS_HINT = "语文/数学/英语/物理/化学/生物/政治/历史/地理"

_JSON_SCHEMA = """{{
    "subject": "九学科之一（{subjects}）",
    "knowledge_points": ["知识点1", "知识点2"],
    "cornell": {{
        "body": "笔记栏：课堂主体内容（markdown，条理化）",
        "summary": "总结栏：一句话~一段概括",
        "cues": [
            {{"question": "线索问题1（可作复习卡正面）", "answer_hint": "对应要点摘要（背面锚点）"}}
        ]
    }}
}}"""

_REQUIREMENTS = """整理要求：
1. subject 必须从九学科中选一；无法判断时按内容推断最接近的学科
2. cues 至少 1 条；线索问题须是「能遮挡回忆」的提问（非陈述句）
3. 若原文无明确线索，生成 1 条默认占位 cue（question 概括全文主旨，标记待用户确认）
4. answer_hint 为该线索对应的笔记栏要点摘要，便于遮挡回忆时提示
5. 字段缺失时填空串或空列表，禁止填 null"""

MULTIMODAL_PROMPT = """你是一位康奈尔笔记整理专家。请直接读取用户提供的图片（对话上传或本地路径），整理为康奈尔三栏结构。

请按以下 JSON 格式输出（不要输出其他内容）：
{json_schema}

{requirements}
"""

TEXT_PROMPT = """你是一位康奈尔笔记整理专家。请对以下笔记文本整理为康奈尔三栏结构。

原始文本：
{raw_text}

请按以下 JSON 格式输出（不要输出其他内容）：
{json_schema}

{requirements}
"""


def render_multimodal_prompt() -> str:
    return MULTIMODAL_PROMPT.format(
        json_schema=_JSON_SCHEMA.format(subjects=SUBJECTS_HINT),
        requirements=_REQUIREMENTS,
    )


def render_text_prompt(raw_text: str) -> str:
    return TEXT_PROMPT.format(
        raw_text=raw_text,
        json_schema=_JSON_SCHEMA.format(subjects=SUBJECTS_HINT),
        requirements=_REQUIREMENTS,
    )
