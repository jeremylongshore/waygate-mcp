# Source security remediation — 2026-11-10

Refs bead bd_000-projects-wcze.12. This is partial remediation, not closure.

Replaced both calculator uses of `eval` with shared bounded AST arithmetic.
Preserved addition, subtraction, multiplication, true/floor division, unary
signs, parentheses and bounded powers. Enforced 256 characters, 64 AST nodes,
16 nesting levels, magnitude at most 10**100 and exponent magnitude at most 100.
Non-real/non-finite results and unsupported syntax fail. Sixteen regression
cases failed before the repair; all 44 calculator cases now pass.

Retained file-search handlers only skip OSError/UnicodeError, and retained
OAuth catalog handlers only tolerate the optional import being absent. Four
regressions reproduced silently swallowed unexpected errors before the repair;
all eight targeted cases now pass. The isolated feature fragments receive the
host exception module in tests; this does not establish standalone packaging.
Additional retained-module tests exercise file roundtrips, search/listing,
required arguments, path boundaries and actual local command exit results.
No provider requests or cloud writes were made.

Full suites: 200 tests pass on Python 3.11 and 3.12, 80.93% branch coverage,
unchanged 80% floor. Importing retained feature modules expanded measured scope
from the previous runtime-only observation; coverage was not reduced or waived.
Configured mypy passes 31 files on both versions; Black/isort/flake8 pass.

Semgrep 1.178.0, using the existing repaired repository rules, exits 0 with
zero findings and zero analysis errors. The JSON report is retained here.
Bandit still fails on seven remaining findings; its retained summary excludes
source snippets/messages. Dependency and historical-secret gates remain open.
Do not interpret the Semgrep result as a complete security assessment.
