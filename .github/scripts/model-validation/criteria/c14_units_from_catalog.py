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
# MS2-14: "units are referenced from the SAMM unit catalog whenever
# possible".
#
# Never FAIL/WARN/INFO, always SKIP: whether a matching catalog unit
# actually exists for a given quantity isn't something this script can
# know (it doesn't load the catalog itself), so a unit that doesn't use
# the 'unit:' prefix - or a custom samm:Unit definition - is not actually
# evidence of a violation, just a fact to point the reviewer at. SKIP
# (rather than WARN) keeps it from claiming a "likely violation" it can't
# substantiate, and out of the "passing" count when nothing is found.

from __future__ import annotations

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-14"
TITLE = "Units reference the SAMM unit catalog (heuristic, needs human review)"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    findings = []
    for el in model.elements.values():
        if el.unit and not el.unit.startswith("unit:"):
            findings.append(Finding(ID, TITLE, "SKIP", model.file,
                                     f"'{el.name}' uses unit '{el.unit}' which is not from the "
                                     f"'unit:' catalog prefix - confirm no catalog unit fits",
                                     element=el.name))
        if el.short_type == "Unit":
            findings.append(Finding(ID, TITLE, "SKIP", model.file,
                                     f"'{el.name}' defines a custom samm:Unit - confirm it does not "
                                     f"already exist in the SAMM unit catalog", element=el.name))
    if not findings:
        # An empty list here would otherwise fall through to ms2_check.py's
        # "silent criterion -> synthesize a passing INFO" fallback, which
        # would undo the point of using SKIP above.
        findings.append(Finding(ID, TITLE, "SKIP", model.file,
                                 "no non-catalog unit references or custom samm:Unit definitions found"))
    return findings
