#!/usr/bin/env python3
"""Fail CI if protected test modules are fully commented-out/no-op."""

from __future__ import annotations

import pathlib
import re
import sys

PROTECTED_SUITES = [
    pathlib.Path("tests/test_mcp_tooling_security.py"),
    pathlib.Path("tests/test_oidc_validation.py"),
]


COMMENT_ONLY = re.compile(r"^\s*(#.*)?$")


def module_is_effectively_commented(path: pathlib.Path) -> bool:
    if not path.exists():
        return True
    lines = path.read_text(encoding="utf-8").splitlines()
    executable = [ln for ln in lines if not COMMENT_ONLY.match(ln)]
    if not executable:
        return True

    # consider module disabled if no active test function definitions are present
    return not any(line.lstrip().startswith("def test_") for line in executable)


def main() -> int:
    failing = [str(p) for p in PROTECTED_SUITES if module_is_effectively_commented(p)]
    if failing:
        print("Protected test module(s) are disabled or fully commented:")
        for path in failing:
            print(f" - {path}")
        return 1

    print("Protected test modules are active.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
