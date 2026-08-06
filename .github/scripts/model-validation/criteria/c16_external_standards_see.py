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
MS2-16: "when relying on external standards, they are referenced through
a 'see' element".

Informational only (INFO, never FAIL/WARN): whether this model *relies
on* an external standard at all is not something that can be inferred
from the file. This just surfaces existing samm:see usage for the
reviewer.
"""

from __future__ import annotations

from ..context import Context
from ..model import TTLModel
from ..report import Finding

ID = "MS2-16"
TITLE = "External standards referenced via samm:see (informational, needs human review)"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    with_see = [el.name for el in model.elements.values() if el.see]
    if with_see:
        return [Finding("MS2-16", TITLE, "INFO", model.file,
                         f"{len(with_see)} element(s) carry a samm:see reference: {with_see}")]
    return [Finding("MS2-16", TITLE, "INFO", model.file,
                     "no samm:see references found - if this model implements/relates to an "
                     "external standard, reference it via samm:see")]
