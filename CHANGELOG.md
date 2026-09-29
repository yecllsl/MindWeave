# Changelog

All notable changes to this project will be documented in this file.

## [0.3.2] - 2026-09-29

### Added

- **仓库根 `marketplace.json`（VS Code / Copilot 远程市场）**：新增 Claude Code / Copilot CLI 同源市场格式清单，插件条目 `source` 指向 `./mindweave.plugin`，使 VS Code 经 `chat.plugins.marketplaces: ["yecllsl/MindWeave"]` 远程市场安装 MindWeave 走通（VS Code 的 Install from Source 要求 `plugin.json` 在仓库根，本仓库插件在子目录，故不能用仓库根/子目录 URL 直装）；`scripts/check_version.py` 已纳入该清单的版本守卫
- **`scripts/check_version.py` 版本一致性校验**：以 `pyproject.toml` 为真相源，覆盖 CHANGELOG 与各插件/市场/AAIF 声明清单的版本一致性，并接入 CI config-drift job
- **CodeBuddy 本地插件市场通道**：新建根级 `.codebuddy-plugin/marketplace.json`（市场 `mindweave-local-market`，单插件）；`mindweave.plugin/.codebuddy-plugin/plugin.json` 补 `mcpServers` 指向可移植 `.mcp.json`（`${CODEBUDDY_PLUGIN_ROOT}` + `uv` 入口，替换原硬编码绝对路径版）

### Changed

- **两层 Harness 策略写入真相源与文档**：Tier 1 — Agent Plugins 1.0 插件标准（代表 VS Code / Copilot，插件形态分发，规范不携带 AGENTS.md）；Tier 2 — 免费额度 / 开箱即用（Trae、OpenCode 原生目录 + 同步脚本）；明确不支持 WorkBuddy / Hermes / Goose
- **术语清理**：「AAIF 真相源 / AAIF 配置层 / AAIF 插件包」等混写统一为「配置唯一真相源」，打包标准统一表述为 Agent Plugins 1.0（AAIF 作为基金会/单项标准的表述保留）
- **MCP 启动去掉 `--no-sync`**：`mindweave.plugin/mcp.json`（Tier 1 插件包）恢复 `uv run` 默认同步行为，插件首启自动构建虚拟环境（Git URL 远程安装场景必需）；Tier 2 的 `.trae/` / `.opencode/` 运行时配置仍保留 `--no-sync`
- **文档层级标注与基线对齐**：README 架构图/技术栈/「支持的 Harness」表、插件 `AGENTS.md` 架构图与生成的根 `AGENTS.md` 统一将 CodeBuddy 表述为 Tier 1 市场通道，不再写作 Tier 2 / 单向同步目标

### Removed

- **Goose 支持**：`.goose/` 目录、`runtime/goose.json`、`scripts/generate-goose-config.py`、sync 的 Goose 分支、check-config-drift 校验项、文档全部引用（历史条目保留）
- **CodeBuddy 原生配置目录**：`.codebuddy/`（AGENTS.md、mcp.json、5 个 Skill）全部删除，仅保留运行时自有数据（memory 等），不再参与同步与漂移校验

## [0.2.0] - 2026-08-30

### 新增
- **AI 出题测验（对话链路）**：`generate_quiz` / `save_quiz` / `grade_quiz` 三工具，选择/填空题型；出题即复习（判分与自评共享 `apply_review` SM-2 更新路径，ReviewRecord 新增 `source` 字段区分 self/quiz 口径）。
- **`mindweave-quiz` skill**（`/quiz` 命令，触发词：出题/考我/练一练/测验）。
- **Web 可视化人工处理面**（`mindweave-web`，FastAPI + Jinja2 + HTMX/Alpine + ECharts）：概览 / 笔记列表+详情 / 笔记编辑+删除（修正 LLM 整理结果，question 变更重置复习状态）/ 自评复习 / 统计五页面；默认本机绑定 127.0.0.1:8003。

### 安全
- quiz 判分三道硬防御：空作答拒绝、占位题（answer 空）拒绝、已判分 quiz 拒绝二次评分。
- `save_quiz` 经 `QuizRecord` pydantic 重建校验（选择题 answer ∈ options），禁止宿主直写 quizzes 文件；`data/quizzes/` 不入 Git。

## [0.1.0] - 2026-08-30

### 首个版本：K12 康奈尔 AI 智能笔记 Agent Plugin

- **服务层**（`mindweave.plugin/mindweave-mcp/`）：Python 3.12+ / FastMCP / Pydantic v2 的标准 MCP server，10 个工具（`organize_note` / `save_note` / `get_note` / `query_notes` / `update_note` / `delete_note` / `schedule_review` / `submit_review` / `get_statistics` / `export_data`）；数据模型（NoteRecord/Cue/Cornell/ReviewState/ReviewRecord）；SM-2 算法（移植 VocabCraft 已验证实现，语义一致、代码独立）；JSON 原子写存储。
- **插件层**（`mindweave.plugin/`）：Agent Plugins 1.0 包（plugin.json / mcp.json）+ 4 个 Skill（capture / review / stats / export）+ 4 份 runtime 配置 + CodeBuddy CLI 身份；AAIF 声明文件（tools/triggers/workflows.json）由 `scripts/generate-aaif-declarations.py` 从真实源自省生成；`scripts/sync-agent-configs` 单向投影到 `.trae/` / `.opencode/` / `.codebuddy/`。
- **仓库级文档**：AGENTS.md（规则层：采集三模式 / cue≥1 / question 变更重置 / 每日 10 卡 / Prompt 防御 / 数据安全）、README.md、本 CHANGELOG、MIT LICENSE。
