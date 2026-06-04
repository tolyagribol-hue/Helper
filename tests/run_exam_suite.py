#!/usr/bin/env python
"""
Главный тест-раннер для экзамена ОП РПМ.
Запуск из корня проекта: python tests/run_exam_suite.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    print("=" * 70)
    print("IT Top Support Bot — тестовый комплекс ОП РПМ")
    print(f"Корень проекта: {PROJECT_ROOT}")
    print("=" * 70)
    print()

    categories = [
        ("Верификация", "tests/test_verification.py"),
        ("Валидация", "tests/test_validation.py"),
        ("Юзабилити", "tests/test_usability.py"),
        ("Производительность", "tests/test_performance.py"),
    ]

    overall = 0
    for name, path in categories:
        print(f"\n--- {name} ({path}) ---\n")
        r = subprocess.run(
            [sys.executable, "-m", "pytest", path, "-v", "--tb=short"],
            cwd=str(PROJECT_ROOT),
        )
        if r.returncode != 0:
            overall = r.returncode

    print("\n" + "=" * 70)
    if overall == 0:
        print("Все категории тестов пройдены.")
    else:
        print("Есть ошибки — см. вывод выше.")
    print("=" * 70)
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
