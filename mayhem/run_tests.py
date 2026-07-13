#!/usr/bin/python3
"""run_tests.py — RUN python-pptx's ENTIRE upstream test suite and print a parseable summary.

Invoked via the `/mayhem/pptx-tests` ELF launcher (NOT directly), so the verify-repo sabotage
oracle can neuter the launcher and prove the test oracle is behavioral (an LD_PRELOAD constructor
_exit(0)s the launcher before the suite runs → no RUNTESTS line → test.sh fails).

This runs the project's OWN upstream suites, unmodified:
  * the pytest unit suite under `tests/` (`py.test -q`), and
  * the behave acceptance/functional suite under `features/` (`behave --tags=-wip`),
which together are exactly what upstream's tox runs (`py.test -qx` + `behave ...`). These are
real behavioral assertions on python-pptx's parsing/serialization — a no-op / exit(0) /
behavior-altering patch to `pptx` makes them fail.

It prints one line:

    RUNTESTS tests=<n> passed=<p> failed=<f> skipped=<s>

Exit 0 iff failed == 0. mayhem/test.sh parses that line into a CTRF report.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

SRC = os.environ.get("SRC", "/mayhem")


def run(cmd):
    print(f"=== running: {' '.join(cmd)} ===", flush=True)
    proc = subprocess.run(cmd, cwd=SRC, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    print(out, flush=True)
    return out, proc.returncode


def parse_pytest(out):
    """Parse pytest's summary line: 'N passed, M failed, K skipped in ...'."""
    passed = failed = skipped = 0
    m = re.search(r"(\d+) passed", out)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+) failed", out)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+) error", out)
    if m:
        failed += int(m.group(1))
    m = re.search(r"(\d+) skipped", out)
    if m:
        skipped = int(m.group(1))
    return passed, failed, skipped


def parse_behave(out):
    """Parse behave's scenario summary: 'N scenarios passed, M failed, K skipped'."""
    passed = failed = skipped = 0
    m = re.search(r"(\d+) scenarios? passed, (\d+) failed(?:, (\d+) skipped)?", out)
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2))
        skipped = int(m.group(3) or 0)
    return passed, failed, skipped


def main() -> int:
    total_p = total_f = total_s = 0
    ran_any = False

    # 1) pytest unit suite.
    out, rc = run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"])
    p, f, s = parse_pytest(out)
    if p + f + s == 0:
        # No summary parsed => the suite did not run (import error / crash). Hard failure.
        print("ERROR: pytest produced no parseable summary", flush=True)
        f = max(f, 1)
    else:
        ran_any = True
    total_p += p
    total_f += f
    total_s += s

    # 2) behave acceptance/functional suite.
    out, rc = run([sys.executable, "-m", "behave", "--no-color", "--format", "plain",
                   "--tags=-wip"])
    p, f, s = parse_behave(out)
    if p + f + s == 0:
        print("ERROR: behave produced no parseable summary", flush=True)
        total_f += 1
    else:
        ran_any = True
        total_p += p
        total_f += f
        total_s += s

    if not ran_any:
        total_f = max(total_f, 1)

    tests = total_p + total_f + total_s
    print(f"RUNTESTS tests={tests} passed={total_p} failed={total_f} skipped={total_s}", flush=True)
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # import/setup failure is a hard failure, not a vacuous pass
        import traceback

        traceback.print_exc()
        print(f"RUNTESTS tests=1 passed=0 failed=1 skipped=0 (harness error: {exc})")
        sys.exit(1)
