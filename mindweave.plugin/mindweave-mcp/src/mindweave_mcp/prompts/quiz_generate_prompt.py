"""AI 出题命题 prompt：选择/填空两题型（宿主 LLM 按 prompt 生成，经 save_quiz 回写）。"""

SELECT_GENERATE_PROMPT = """你是一位 K12 出题专家。请根据以下康奈尔笔记知识卡生成一道选择题。

学科：{subject}
线索问题（知识卡正面）：{question}
参考答案要点：{answer_hint}
笔记栏摘录：
{body_excerpt}
干扰项素材（同学科其他知识卡的线索问题，可改编为错误表述）：
{distractor_pool}

要求：
1. 题干基于线索问题或笔记栏内容，语言适合 K12 学生
2. 生成 4 个选项（1 个正确 + 3 个干扰），干扰项应与正确答案同学科、语义相近、具备迷惑性
3. answer 必须与 options 中某一项完全一致

请只输出 JSON，不要输出其他内容：
{{
    "question": "题干文本",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "正确答案（须与某选项完全一致）"
}}
"""

FILL_GENERATE_PROMPT = """你是一位 K12 出题专家。请根据以下康奈尔笔记知识卡生成一道填空题。

学科：{subject}
线索问题（知识卡正面）：{question}
参考答案要点：{answer_hint}
笔记栏摘录：
{body_excerpt}

要求：
1. 题干为一句话或短段落，将答案关键处挖空（用 ______ 表示空缺）
2. 挖空处应能由 answer_hint 中的核心要点作答
3. answer 填参考答案要点（answer_hint 的核心表述）

请只输出 JSON，不要输出其他内容：
{{
    "question": "含 ______ 空缺的题干",
    "options": null,
    "answer": "参考答案要点"
}}
"""
