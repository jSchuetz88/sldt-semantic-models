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
MS2-22: "all contributors to this model are mentioned in copyright header
of model file".

Informational only (INFO, never FAIL/WARN): copyright headers name
contributing *organizations*, while git authorship only gives GitHub
account names, which don't map 1:1 to those organizations. This just
surfaces both lists side by side for the reviewer to compare.
"""

from __future__ import annotations

import re

from ..context import Context
from ..model import TTLModel
from ..report import Finding

TITLE = "Contributors mentioned in copyright header (needs human review)"
COPYRIGHT_LINE_RE = re.compile(r"#\s*Copyright\(?c\)?\s+\d{4}\s+(.+?)\s*$", re.MULTILINE)


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    header_match = re.match(r"(?:#.*\n)+", model.text)
    header = header_match.group(0) if header_match else ""
    copyright_holders = COPYRIGHT_LINE_RE.findall(header)

    authors = ctx.commit_authors(model.file)

    return [Finding(
        "MS2-22", TITLE, "INFO", model.file,
        f"copyright header lists: {copyright_holders or '(none found)'}; git commit authors for "
        f"this file in this PR: {authors or '(none found)'}. GitHub author names don't map 1:1 to "
        f"the company names used in headers, so please confirm manually that every contributing "
        f"organization is represented.",
    )]
