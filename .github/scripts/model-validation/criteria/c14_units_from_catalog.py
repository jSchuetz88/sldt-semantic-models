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
MS2-14: "units are referenced from the SAMM unit catalog whenever
possible".

Heuristic only (WARN, not FAIL): flags samm:unit values that don't use
the catalog's 'unit:' prefix, and custom samm:Unit definitions. Whether a
matching catalog unit actually exists is left to the reviewer.
"""

from __future__ import annotations

from ..context import Context
from ..model import TTLModel
from ..report import Finding

ID = "MS2-14"
TITLE = "Units reference the SAMM unit catalog (heuristic, needs human review)"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    findings = []
    for el in model.elements.values():
        if el.unit and not el.unit.startswith("unit:"):
            findings.append(Finding("MS2-14", TITLE, "WARN", model.file,
                                     f"'{el.name}' uses unit '{el.unit}' which is not from the "
                                     f"'unit:' catalog prefix - confirm no catalog unit fits",
                                     element=el.name))
        if el.short_type == "Unit":
            findings.append(Finding("MS2-14", TITLE, "WARN", model.file,
                                     f"'{el.name}' defines a custom samm:Unit - confirm it does not "
                                     f"already exist in the SAMM unit catalog", element=el.name))
    return findings
