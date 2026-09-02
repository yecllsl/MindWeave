---
name: mindweave-review
description: Use when 用户想复习笔记、该复习了、复习到期知识卡。NOT for 录入新笔记（用 mindweave-capture）、出题测验（用 mindweave-quiz，测验是出题判分，复习是自评，二者都推进 SM-2）、查看统计（用 mindweave-stats）、导出（用 mindweave-export）
---

# 笔记复习流程

## Overview
按 SM-2 到期队列逐卡遮挡回忆自评。核心流程：**schedule_review 取到期卡 → 逐卡「线索问题 → 用户回忆 → 揭示 answer_hint+笔记栏 → 自评 1-4」→ submit_review → 汇总**。

## When to Use
- 用户说"复习笔记"、"该复习了"、"复习到期的知识卡"

## Workflow

### 1. 取到期队列
调用 `schedule_review`（可选 `subject` 过滤）。每日上限 10 卡。

### 2. 逐卡复习
对每张到期卡：
1. 展示 `question`，让用户遮挡回忆
2. 用户回忆后揭示 `answer_hint` + 对应笔记栏
3. 用户自评 1-4（4 轻松想起 / 3 勉强想起 / 2 模糊 / 1 想不起）

### 3. 提交评分
调用 `submit_review`（传 `cue_id` 与用户自评 `grade` 1-4）。

### 4. 汇总
输出：复习卡数、grade 分布、grade<3 薄弱卡清单、下次复习日期分布。

## Common Mistakes
- **评分主观化**：1-4 档客观评分，禁因情绪调整
- **跳过需记录原因**：跳过不延后日期，需记录原因
- **一次并行 submit 多卡**：cue 的 review_state 更新依赖当前值，须逐卡顺序提交

## Red Flags
- 不经用户回忆就直接 submit_review
- grade 超出 1-4 范围
