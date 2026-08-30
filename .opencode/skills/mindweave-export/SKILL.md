---
name: mindweave-export
description: Use when 用户想导出笔记、备份笔记。NOT for 录入（用 mindweave-capture）、复习（用 mindweave-review）、统计（用 mindweave-stats）
---

# 笔记导出流程

## When to Use
- 用户说"导出笔记"、"备份"

## Workflow
调用 `export_data(format=...)`（`json` 或 `markdown`），导出前须经用户确认。

## Common Mistakes
- **未经确认就导出**
