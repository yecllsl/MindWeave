#!/usr/bin/env python3
"""版本一致性校验 —— AGENTS.md「质量与合规规则 > 文档」的机械防线

真相源：`mindweave.plugin/mindweave-mcp/pyproject.toml` 的 `[project].version`。

校验项：
    1. CHANGELOG.md 最新条目版本
    2. 清单类文件：根 package.json / plugin.json（主 + CodeBuddy 副本）/ 两个 marketplace.json / tools.json
    3. （可选 --tag）发布 tag 与真相源一致，防止打错 tag

MindWeave 不在 `__init__.py` 硬编码版本（AGENTS.md 文档规则未要求），也不在文档中嵌入
版本化发行包名，故仅校验 CHANGELOG 与清单类文件，避免误报。

用法：
    python scripts/check_version.py              # 校验文档与清单
    python scripts/check_version.py --tag v0.3.2 # 额外校验发布 tag
退出码：0 全部一致；1 存在不一致。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "mindweave.plugin" / "mindweave-mcp" / "pyproject.toml"

# 清单类文件的版本路径（键为相对路径，值为从 JSON 根到版本的键序列；int 表示数组下标）
MANIFEST_VERSIONS: list[tuple[str, tuple[str | int, ...]]] = [
    ("package.json", ("version",)),
    ("mindweave.plugin/plugin.json", ("version",)),
    ("mindweave.plugin/.codebuddy-plugin/plugin.json", ("version",)),
    (".codebuddy-plugin/marketplace.json", ("plugins", 0, "version")),
    ("marketplace.json", ("plugins", 0, "version")),
    ("mindweave.plugin/tools.json", ("version",)),
]


def scan_manifests(expected: str) -> list[str]:
    """校验插件/市场/声明清单的版本号，返回不一致项描述"""
    problems: list[str] = []
    for rel, keys in MANIFEST_VERSIONS:
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: 文件不存在")
            continue
        try:
            node: object = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{rel}: JSON 解析失败（{exc}）")
            continue
        found: object = None
        for key in keys:
            if (isinstance(node, dict) and isinstance(key, str) and key in node) or (
                isinstance(node, list) and isinstance(key, int) and key < len(node)
            ):
                node = node[key]
            else:
                node = None
                break
            found = node
        if not isinstance(found, str):
            problems.append(f"{rel}: 未找到版本字段 {'/'.join(map(str, keys))}")
        elif found != expected:
            problems.append(f"{rel}: 版本为 {found}，应为 {expected}")
    return problems


def source_version() -> str:
    """从 pyproject.toml 读取真相源版本"""
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def changelog_version() -> str | None:
    """取 CHANGELOG.md 中最新的 `## [X.Y.Z]` 条目"""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description="校验版本号在各处保持一致")
    parser.add_argument("--tag", help="发布 tag（形如 v0.3.2 或 0.3.2）")
    args = parser.parse_args()

    expected = source_version()
    problems = scan_manifests(expected)

    changelog = changelog_version()
    if changelog is None:
        problems.append("CHANGELOG.md 未找到形如 `## [X.Y.Z]` 的版本条目")
    elif changelog != expected:
        problems.append(f"CHANGELOG.md 最新条目为 {changelog}，应为 {expected}")

    if args.tag:
        tag = args.tag.lstrip("v")
        if tag != expected:
            problems.append(f"发布 tag 为 v{tag}，但 pyproject.toml 为 {expected}")

    if problems:
        print(f"版本不一致（真相源 pyproject.toml = {expected}）：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\n修正后重试；真相源本身需变更时，请先改 pyproject.toml。", file=sys.stderr)
        return 1

    print(f"版本一致性校验通过：{expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
