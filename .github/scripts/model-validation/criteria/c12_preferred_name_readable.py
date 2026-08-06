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
MS2-12: "preferredName should be human readable and follow normal
orthography (e.g., no camel case but normal word separation)".
"""

from __future__ import annotations

import re

from ..context import Context
from ..model import TTLModel
from ..report import Finding

ID = "MS2-12"
TITLE = "preferredName is human-readable (not Camel-Case)"
CAMEL_HUMP_RE = re.compile(r"[a-z][A-Z]")


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    findings = []
    for el in model.elements.values():
        pn = el.preferred_name("en")
        if pn and " " not in pn and CAMEL_HUMP_RE.search(pn):
            findings.append(Finding("MS2-12", TITLE, "FAIL", model.file,
                                     f"preferredName '{pn}' of '{el.name}' looks Camel-Case, "
                                     f"expected normal word separation",
                                     element=el.name))
    return findings
