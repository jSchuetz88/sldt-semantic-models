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
# Finding data structure and report rendering shared by all criteria.

from __future__ import annotations

from dataclasses import dataclass

# FAIL   -> objectively violates a MS2 rule, breaks the CI check
# WARN   -> rule is only partially machine-checkable (heuristic) or the
#           finding is a likely-but-not-certain violation; does not break CI
# INFO   -> a genuine automated pass: this was actually checked and nothing
#           is wrong
# NOTE   -> the criterion can never render a pass/fail verdict at all (the
#           question isn't machine-answerable from the file), so this is
#           just a fact for the reviewer, not a confirmation of anything.
#           Treated the same as INFO for blocking/summary-counting purposes
#           - the distinction is for the reader, not the gate - but gets a
#           different icon so a real automated pass isn't visually
#           confused with "nothing to check here, please review manually".
# SKIP   -> criterion could not be evaluated (e.g. missing external tool)
LEVELS = ("FAIL", "WARN", "INFO", "NOTE", "SKIP")


@dataclass
class Finding:
    criterion_id: str
    title: str
    level: str
    file: str
    message: str
    element: str | None = None

    def __str__(self) -> str:
        loc = f"{self.file}" + (f" [{self.element}]" if self.element else "")
        return f"{self.level:<4} {self.criterion_id} {loc}: {self.message}"


def has_failures(findings: list[Finding]) -> bool:
    return any(f.level == "FAIL" for f in findings)


# Table icon per level: check = genuine automated pass, info = non-
# evaluable fact for the reviewer, warning = non-blocking heads-up, cross =
# blocking failure, dash = doesn't matter right now (skipped/disabled/
# couldn't run).
ICON = {"FAIL": "❌", "WARN": "⚠️", "INFO": "✅", "NOTE": "ℹ️", "SKIP": "➖"}


def _flatten(text: str) -> str:
    return text.replace("\n", " ")


def _escape_cell(text: str) -> str:
    return _flatten(text).replace("|", "\\|")


def _code_cell(text: str) -> str:
    # Wraps a table cell's content in an inline code span so it renders in
    # monospace - real line breaks don't survive inside a table cell, but
    # at least indentation/alignment reads better than flowing prose. `|`
    # doesn't need escaping inside a code span (GFM tables don't treat it
    # as a cell separator there); a literal backtick would end the span
    # early though, so that one still needs handling.
    return f"`{_flatten(text).replace('`', chr(39))}`"


def render_markdown(findings: list[Finding], files_checked: list[str]) -> str:
    lines = ["# MS2 Criteria Report", ""]

    if not files_checked:
        lines.append("No `.ttl` files were changed in this PR.")
        return "\n".join(lines)

    by_file: dict[str, list[Finding]] = {}
    for finding in findings:
        by_file.setdefault(finding.file, []).append(finding)

    for file in files_checked:
        file_findings = by_file.get(file, [])

        lines.append(f"## MS2 Criteria — {file}")
        lines.append("")

        counts = {level: sum(1 for f in file_findings if f.level == level) for level in LEVELS}
        lines.append(
            f"**Summary:** {counts['FAIL']} failing, {counts['WARN']} warnings, "
            f"{counts['INFO'] + counts['NOTE']} passing, {counts['SKIP']} skipped."
        )
        lines.append("")

        lines.append("| | ID | Criterion | Message |")
        lines.append("|---|---|---|---|")

        by_criterion: dict[str, list[Finding]] = {}
        for finding in file_findings:
            by_criterion.setdefault(finding.criterion_id, []).append(finding)

        for criterion_id in sorted(by_criterion):
            group = by_criterion[criterion_id]
            worst = min(group, key=lambda f: LEVELS.index(f.level))
            messages = "<br>".join(_code_cell(f.message) for f in group)
            lines.append(f"| {ICON[worst.level]} | {criterion_id} | {_escape_cell(group[0].title)} | {messages} |")

        lines.append("")

    return "\n".join(lines)


def render_detected_models(files: list[str]) -> str:
    lines = ["# Detected Models", ""]
    if not files:
        lines.append("No `.ttl` files changed in this PR - MS2 criteria check skipped.")
        return "\n".join(lines)

    lines.append(f"{len(files)} model file(s) changed, one MS2 Criteria check each:")
    lines.append("")
    for f in files:
        lines.append(f"- `{f}`")
    return "\n".join(lines)


def print_console(findings: list[Finding]) -> None:
    for finding in findings:
        print(finding)
