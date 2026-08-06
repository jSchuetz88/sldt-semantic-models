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


# Table icon per level: check = nothing wrong, warning = non-blocking
# heads-up, cross = blocking failure, dash = doesn't matter right now
# (skipped/disabled/couldn't run).
ICON = {"FAIL": "❌", "WARN": "⚠️", "INFO": "✅", "SKIP": "➖"}


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


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
            f"{counts['INFO']} passing, {counts['SKIP']} skipped."
        )
        lines.append("")

        lines.append("| | ID | Criterion | Message |")
        lines.append("|---|---|---|---|")

        by_criterion: dict[str, list[Finding]] = {}
        for finding in file_findings:
            by_criterion.setdefault(finding.criterion_id, []).append(finding)

        # Multi-line messages (e.g. a full samm-cli error dump) would get
        # squashed into a single, hard-to-read line if put straight into a
        # table cell - table rows can't contain real line breaks. Those go
        # into a collapsible <details> block below the table instead, with
        # just a short pointer left in the cell.
        details_blocks: list[tuple[str, str, str]] = []

        for criterion_id in sorted(by_criterion):
            group = by_criterion[criterion_id]
            worst = min(group, key=lambda f: LEVELS.index(f.level))

            cell_parts = []
            for f in group:
                if "\n" in f.message:
                    summary = f.message.split("\n", 1)[0].rstrip(":")
                    cell_parts.append(f"{_escape_cell(summary)} — see details below")
                    details_blocks.append((criterion_id, group[0].title, f.message))
                else:
                    cell_parts.append(_escape_cell(f.message))
            messages = "<br>".join(cell_parts)
            lines.append(f"| {ICON[worst.level]} | {criterion_id} | {_escape_cell(group[0].title)} | {messages} |")

        lines.append("")

        for criterion_id, title, full_text in details_blocks:
            # Not using <details>/<summary> here: GitHub's job-summary
            # sanitizer strips raw HTML tags like <details> entirely (the
            # element doesn't even show up in the DOM), so a collapsible
            # section isn't an option in this context - plain Markdown it is.
            lines.append(f"**{criterion_id} {title} — full output:**")
            lines.append("")
            lines.append("```")
            lines.append(full_text)
            lines.append("```")
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
