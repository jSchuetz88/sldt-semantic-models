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
# INFO   -> nothing wrong found, but a note useful for the human reviewer
# SKIP   -> criterion could not be evaluated (e.g. missing external tool)
LEVELS = ("FAIL", "WARN", "INFO", "SKIP")


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


def render_markdown(findings: list[Finding], files_checked: list[str]) -> str:
    lines = ["# MS2 Criteria Report", ""]

    if not files_checked:
        lines.append("No `.ttl` files were changed in this PR.")
        return "\n".join(lines)

    lines.append("Checked files:")
    for f in files_checked:
        lines.append(f"- `{f}`")
    lines.append("")

    counts = {level: sum(1 for f in findings if f.level == level) for level in LEVELS}
    lines.append(
        f"**Summary:** {counts['FAIL']} failing, {counts['WARN']} warnings, "
        f"{counts['INFO']} notes, {counts['SKIP']} skipped."
    )
    lines.append("")

    by_criterion: dict[str, list[Finding]] = {}
    for finding in findings:
        by_criterion.setdefault(finding.criterion_id, []).append(finding)

    icon = {"FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️", "SKIP": "⏭️"}

    for criterion_id in sorted(by_criterion):
        group = by_criterion[criterion_id]
        worst = min(group, key=lambda f: LEVELS.index(f.level))
        lines.append(f"## {icon[worst.level]} {criterion_id} — {group[0].title}")
        for entry in group:
            loc = f"`{entry.file}`" + (f" — `{entry.element}`" if entry.element else "")
            lines.append(f"- {icon[entry.level]} **{entry.level}** {loc}: {entry.message}")
        lines.append("")

    return "\n".join(lines)


def print_console(findings: list[Finding]) -> None:
    for finding in findings:
        print(finding)
