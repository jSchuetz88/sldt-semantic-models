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
# MS2-21: "file RELEASE_NOTES.md exists and contains entries for proposed
# model changes".

from __future__ import annotations

import re
from pathlib import Path

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-21"
TITLE = "RELEASE_NOTES.md exists and documents this version"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    if not model.namespace:
        return [Finding(ID, TITLE, "FAIL", model.file, "could not determine this model's namespace")]

    release_notes = Path(model.namespace) / "RELEASE_NOTES.md"
    if not release_notes.exists():
        return [Finding(ID, TITLE, "FAIL", model.file, f"{release_notes} does not exist")]

    findings = []
    text = release_notes.read_text(encoding="utf-8")
    if model.version and not re.search(re.escape(f"[{model.version}]"), text):
        findings.append(Finding(ID, TITLE, "WARN", model.file,
                                 f"{release_notes} has no entry mentioning '[{model.version}]'"))
    if str(release_notes) not in ctx.changed_files:
        findings.append(Finding(ID, TITLE, "WARN", model.file,
                                 f"{release_notes} was not modified in this PR - verify it already "
                                 f"documents this change"))
    if not findings:
        findings.append(Finding(ID, TITLE, "INFO", model.file,
                                 f"{release_notes} was updated and mentions version {model.version}"))
    return findings
