#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 tools/ 下的脚本只使用标准库。

原理：对每个顶层 import 用 importlib.util.find_spec 定位模块，
若其文件路径落在 site-packages / dist-packages 下，即为第三方包。

这比 sys.stdlib_module_names 兼容性更好（后者 Python 3.10 才引入），
也更准确——它判断的是"这个模块从哪来"，而不是"名字在不在白名单里"。

退出码：0 = 仅标准库 · 1 = 发现第三方依赖
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import sys

# 仓库内的本地模块，不算第三方
LOCAL = {"apr_calculator", "scheme_audit", "report_builder"}
# 第三方包安装目录的典型特征
SITE_MARKERS = ("site-packages", "dist-packages", ".venv", "virtualenv")


def is_third_party(root: str) -> bool:
    try:
        spec = importlib.util.find_spec(root)
    except (ImportError, ValueError, ModuleNotFoundError):
        return False
    if spec is None or not spec.origin:
        return False
    origin = spec.origin.replace("\\", "/").lower()
    return any(m in origin for m in SITE_MARKERS)


def main() -> int:
    tools = pathlib.Path("tools")
    if not tools.is_dir():
        print("找不到 tools/ 目录，请在仓库根目录运行")
        return 1

    bad: list[str] = []
    checked = 0

    for py in sorted(tools.glob("*.py")):
        checked += 1
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif (isinstance(node, ast.ImportFrom)
                  and node.module and node.level == 0):
                roots = [node.module.split(".")[0]]
            for root in roots:
                if root in LOCAL:
                    continue
                if is_third_party(root):
                    bad.append("%s: %s" % (py.name, root))

    if bad:
        print("发现第三方依赖（本项目要求零依赖）：")
        for b in sorted(set(bad)):
            print("  -", b)
        return 1

    print("OK：%d 个脚本，仅使用标准库" % checked)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
