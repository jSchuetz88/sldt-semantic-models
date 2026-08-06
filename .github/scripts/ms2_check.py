#!/usr/bin/env python3
#######################################################################
# Copyright (c) 2026 Catena-X Automotive Network e.V.
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This work is made available under the terms of the
# Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
# which is available at
# https://creativecommons.org/licenses/by/4.0/legalcode.
#
# SPDX-License-Identifier: CC-BY-4.0
#######################################################################
"""
Master script for the MS2 criteria check (see .github/PULL_REQUEST_TEMPLATE.md).

This is the single entry point triggered by CI on every pull request (see
.github/workflows/ms2-criteria-check.yml). Its only job is to:

  1. Find out which .ttl files this PR changed.
  2. Parse each one into a TTLModel (.github/scripts/model-validation/model.py).
  3. Hand that model + a shared Context to every criterion sub-routine
     registered in .github/scripts/model-validation/criteria/.
  4. Collect all Findings, print/report them, and fail the job if any
     criterion reports a FAIL-level finding.

It intentionally does none of the actual rule-checking itself - each MS2
checklist item lives in its own sub-routine under criteria/, which is
where you extend this when a criterion is added or changes. See the
package docstring there for details.

Usage (run from the repository root, mirrors check-model-states.py):
    python .github/scripts/ms2_check.py [--base-branch origin/main]
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# The package directory is named "model-validation" (matching the naming of
# .github/actions/model-validation), which is not a valid Python identifier,
# so it can't be the target of a static `from model-validation import ...`
# statement - it has to be loaded dynamically instead.
_pkg = importlib.import_module("model-validation")
criteria = importlib.import_module("model-validation.criteria")
report = importlib.import_module("model-validation.report")
Context = importlib.import_module("model-validation.context").Context
parse_model = importlib.import_module("model-validation.model").parse_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-branch",
        default=os.environ.get("MS2_BASE_BRANCH", "origin/main"),
        help="Branch to diff against to find changed .ttl files (default: origin/main)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()

    ctx = Context(repo_root=repo_root, base_branch=args.base_branch)
    changed_ttl_files = ctx.check_model_states.get_changed_ttl_files(args.base_branch)
    ctx.changed_files = changed_ttl_files

    if not changed_ttl_files:
        print("No .ttl files changed - nothing to check for MS2 criteria.")
        _write_step_summary(report.render_markdown([], []))
        return 0

    all_findings: list[report.Finding] = []
    for ttl_file in changed_ttl_files:
        print(f"\n=== MS2 criteria for {ttl_file} ===")
        model = parse_model(ttl_file)
        for check_fn in criteria.REGISTRY:
            findings = check_fn(model, ctx)
            all_findings.extend(findings)
            report.print_console(findings)

    markdown = report.render_markdown(all_findings, changed_ttl_files)
    _write_step_summary(markdown)

    if report.has_failures(all_findings):
        print("\nMS2 criteria check FAILED - see FAIL entries above.")
        return 1

    print("\nMS2 criteria check passed (WARN/INFO entries may still need human review).")
    return 0


def _write_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(markdown)
        f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
