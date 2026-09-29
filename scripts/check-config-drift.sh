#!/bin/sh
# scripts/check-config-drift.sh — 检查 Tier 2 平台生成目录是否与 mindweave.plugin 真相源一致
#
# 用途：CI config-drift job 与本地巡检。与 pre-commit 钩子互为补充：
#   - pre-commit 钩子查「暂存区」，拦截提交那一刻的违规
#   - 本脚本查「工作区」，作为无本地钩子时的 CI 兜底（例如绕过钩子 push）
#
# 检查范围（与 pre-commit 一致）：Tier 2 平台（.trae / .opencode）的 skills/** 与 AGENTS.md
# 必须与其 mindweave.plugin/ 源逐字节一致（Trae 平台额外校验根 AGENTS.md——Trae 读取
# 项目根 AGENTS.md，由同步脚本从 mindweave.plugin/AGENTS.md 复制而来）；
# 非纯复制产物（mcp.json / opencode.json / .ignore 等）豁免。
# 以 mindweave.plugin 为权威遍历，因此同时覆盖「直改平台副本」与「改源忘同步（缺同步）」两类漂移。
#
# 注：CodeBuddy / VS Code 走 Tier 1 插件通道（mindweave.plugin/ Agent Plugins 1.0 包），
# 不再生成 .codebuddy/ 原生目录，故此处不校验 .codebuddy。

set -eu

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

tmp=".git/check-drift.$$"
trap 'rm -f "$tmp"' EXIT

violations=0

# 比较生成文件与源；不一致则计数并报告
check_pair() {  # $1=生成文件, $2=源
    if ! cmp -s "$1" "$2"; then
        echo "漂移: $1 与真相源 $2 不一致" >&2
        violations=$((violations + 1))
    fi
}

# AGENTS.md：Trae 平台读取项目根 AGENTS.md，其余平台各有自己的副本。
# 采用「平台有则必须与源一致」，而不要求平台必须有。
for copy in AGENTS.md .opencode/AGENTS.md; do
    if [ -f "$copy" ]; then
        check_pair "$copy" "mindweave.plugin/AGENTS.md"
    fi
done

# skills/**：以 mindweave.plugin/skills 为权威，检查 Tier 2 平台副本存在且一致
find mindweave.plugin/skills -type f > "$tmp"
while IFS= read -r f || [ -n "$f" ]; do
    if [ -z "$f" ]; then
        continue
    fi
    for p in .trae .opencode; do
        copy="$p${f#mindweave.plugin}"    # mindweave.plugin/skills/x → $p/skills/x（POSIX 前缀剔除，兼容 dash）
        if [ ! -f "$copy" ]; then
            echo "漂移: $p 缺少同步文件 $copy（源 $f 未同步到 $p）" >&2
            violations=$((violations + 1))
        else
            check_pair "$copy" "$f"
        fi
    done
done < "$tmp"

if [ "$violations" -gt 0 ]; then
    echo "配置漂移: $violations 处不一致。请运行 scripts/sync-agent-configs.sh（或 .ps1）同步后重新检查。" >&2
    exit 1
fi

echo "config-drift: Tier 2 平台配置与 mindweave.plugin 真相源一致"
exit 0
