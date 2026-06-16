"""Objective grader for the agent-harness experiment.

The agent's job is to produce a ``solution.py`` in its workspace implementing a list of
small, unambiguous features. Each feature is graded by a deterministic check that imports the
agent's module fresh and asserts behaviour. The score is simply: how many features pass.

This module is the *reusable eval* — both the baseline and intervention arms are graded by
the exact same checks, so the only thing that differs between arms is the harness strategy.

`run_checks` is used in two places:
  - as the agent-facing ``run_tests`` tool (returns pass/fail per feature, like CI), and
  - as the final official grade.
Same checks both times — there is no hidden/visible split here; the controlled variable is
the harness, not information about the tests.
"""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from typing import Callable

# Each grader: (feature_id, human name, check function). The check receives the imported
# solution module and must return True iff the feature is correct. Any exception => fail.
Check = Callable[[object], bool]


def _c(fn: Check) -> Check:
    """Wrap a check so any exception (missing attr, crash, wrong type) counts as a fail."""

    def safe(mod: object) -> bool:
        try:
            return bool(fn(mod))
        except Exception:
            return False

    return safe


GRADERS: list[tuple[str, str, Check]] = [
    ("f01", "slugify", _c(lambda m: (
        m.slugify("  Hello, World!  ") == "hello-world"
        and m.slugify("Foo_Bar 123") == "foo-bar-123"
        and m.slugify("Multiple   spaces!!!") == "multiple-spaces"
    ))),
    ("f02", "word_count", _c(lambda m: (
        m.word_count("The cat the CAT") == {"the": 2, "cat": 2}
        and m.word_count("a a a b") == {"a": 3, "b": 1}
    ))),
    ("f03", "is_palindrome", _c(lambda m: (
        m.is_palindrome("A man, a plan, a canal: Panama") is True
        and m.is_palindrome("hello") is False
        and m.is_palindrome("No 'x' in Nixon") is True
    ))),
    ("f04", "roman_to_int", _c(lambda m: (
        m.roman_to_int("IV") == 4
        and m.roman_to_int("MCMXCIV") == 1994
        and m.roman_to_int("III") == 3
    ))),
    ("f05", "int_to_roman", _c(lambda m: (
        m.int_to_roman(4) == "IV"
        and m.int_to_roman(1994) == "MCMXCIV"
        and m.int_to_roman(9) == "IX"
    ))),
    ("f06", "fibonacci", _c(lambda m: (
        m.fibonacci(0) == 0 and m.fibonacci(1) == 1 and m.fibonacci(10) == 55
    ))),
    ("f07", "is_prime", _c(lambda m: (
        m.is_prime(2) is True
        and m.is_prime(1) is False
        and m.is_prime(97) is True
        and m.is_prime(100) is False
    ))),
    ("f08", "flatten", _c(lambda m: (
        m.flatten([1, [2, [3, 4], 5]]) == [1, 2, 3, 4, 5]
        and m.flatten([]) == []
        and m.flatten([[1], [2, [3]]]) == [1, 2, 3]
    ))),
    ("f09", "chunk", _c(lambda m: (
        m.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
        and m.chunk([], 3) == []
    ))),
    ("f10", "caesar_cipher", _c(lambda m: (
        m.caesar_cipher("abc", 1) == "bcd"
        and m.caesar_cipher("XYZ", 3) == "ABC"
        and m.caesar_cipher("Hello, World!", 13) == "Uryyb, Jbeyq!"
    ))),
    ("f11", "to_snake_case", _c(lambda m: (
        m.to_snake_case("CamelCase") == "camel_case"
        and m.to_snake_case("myVariableName") == "my_variable_name"
    ))),
    ("f12", "gcd", _c(lambda m: (
        m.gcd(12, 18) == 6 and m.gcd(17, 5) == 1 and m.gcd(0, 5) == 5
    ))),
    ("f13", "lcm", _c(lambda m: (
        m.lcm(4, 6) == 12 and m.lcm(21, 6) == 42 and m.lcm(0, 5) == 0
    ))),
    ("f14", "factorial", _c(lambda m: (
        m.factorial(0) == 1 and m.factorial(1) == 1 and m.factorial(5) == 120
    ))),
    ("f15", "reverse_words", _c(lambda m: (
        m.reverse_words("the quick brown") == "brown quick the"
        and m.reverse_words("hello") == "hello"
    ))),
    ("f16", "count_vowels", _c(lambda m: (
        m.count_vowels("Hello World") == 3
        and m.count_vowels("xyz") == 0
        and m.count_vowels("AEIOU") == 5
    ))),
    ("f17", "title_case", _c(lambda m: (
        m.title_case("hELLo wORLd") == "Hello World" and m.title_case("foo") == "Foo"
    ))),
    ("f18", "is_anagram", _c(lambda m: (
        m.is_anagram("Listen", "Silent") is True
        and m.is_anagram("a", "b") is False
        and m.is_anagram("Dormitory", "Dirty Room") is True
    ))),
    ("f19", "unique", _c(lambda m: (
        m.unique([1, 2, 1, 3, 2]) == [1, 2, 3] and m.unique([]) == []
    ))),
    ("f20", "rle_encode", _c(lambda m: (
        m.rle_encode("aaabbc") == "a3b2c1"
        and m.rle_encode("") == ""
        and m.rle_encode("a") == "a1"
    ))),
]


def _import_solution(workspace: Path):
    """Import the agent's solution.py fresh (no module caching across grades)."""
    sol = Path(workspace) / "solution.py"
    if not sol.exists():
        return None
    mod_name = f"_sol_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, sol)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # may raise on syntax error -> caller treats as all-fail
    return module


def run_checks(workspace: Path, n_features: int) -> dict:
    """Grade the first ``n_features`` features in the workspace's solution.py.

    Returns {"passed": int, "total": int, "per_feature": [{"id","name","passed"}...]}.
    A missing or unimportable solution.py grades as zero passed.
    """
    graders = GRADERS[:n_features]
    try:
        module = _import_solution(workspace)
    except Exception:
        module = None

    per_feature = []
    for fid, name, check in graders:
        ok = bool(check(module)) if module is not None else False
        per_feature.append({"id": fid, "name": name, "passed": ok})

    return {
        "passed": sum(1 for f in per_feature if f["passed"]),
        "total": len(graders),
        "per_feature": per_feature,
    }


def summary_text(result: dict) -> str:
    """Compact CI-style summary for feeding back to the agent as a tool result."""
    lines = [f"{result['passed']}/{result['total']} features passing:"]
    for f in result["per_feature"]:
        lines.append(f"  [{'PASS' if f['passed'] else 'FAIL'}] {f['id']} {f['name']}")
    return "\n".join(lines)
