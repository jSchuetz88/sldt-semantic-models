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
"""MS2-05: "the identifier for properties starts with a small letter"."""

from __future__ import annotations

from ..context import Context
from ..model import TTLModel
from ..report import Finding
from ._shared import element_findings

ID = "MS2-05"
TITLE = "Property identifiers start with a lowercase letter"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    def bad(el):
        if el.short_type != "Property" or not el.name:
            return None
        return None if el.name[0].islower() else "does not start with a lowercase letter"

    return element_findings("MS2-05", TITLE, model, bad,
                             lambda el, msg: f"property '{el.name}' {msg}")
