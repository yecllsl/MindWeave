---
name: mindweave-stats
description: Use when 用户想看笔记统计、知识点分布、掌握度分布。NOT for 录入（用 mindweave-capture）、复习（用 mindweave-review）、导出（用 mindweave-export）
---

# 笔记统计流程

## When to Use
- 用户说"笔记统计"、"知识点分布"、"掌握度"

## Workflow
调用 `get_statistics(group_by=...)`，支持 `subject` / `knowledge_point` / `date` / `mastery` 四维度。

## Common Mistakes
- **group_by 传非法值**：须为四维度之一
