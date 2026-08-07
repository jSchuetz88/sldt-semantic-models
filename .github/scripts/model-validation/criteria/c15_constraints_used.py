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
# MS2-15: "use constraints to make known constraints from the use case
# explicit in the aspect model".
#
# Informational only (INFO, never FAIL/WARN): whether constraints are
# *missing* for a given use case cannot be determined from the model file
# alone, so this just surfaces what's there for the reviewer - it stays
# INFO (and counts as "passing") either way. The "nothing found" case gets
# a distinct ℹ️ table icon instead of the default ✅ so it doesn't read as
# a verified pass, just a heads-up worth a glance.

from __future__ import annotations

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-15"
TITLE = "Constraints used where applicable (informational, needs human review)"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    constrained = [el.name for el in model.elements.values() if el.short_type.endswith("Constraint")]
    if constrained:
        return [Finding(ID, TITLE, "INFO", model.file,
                         f"{len(constrained)} constraint(s) defined: {constrained}")]
    return [Finding(ID, TITLE, "INFO", model.file,
                     "no samm-c constraints found - if the use case has known constraints "
                     "(ranges, patterns, lengths, ...), consider making them explicit",
                     icon="ℹ️")]
