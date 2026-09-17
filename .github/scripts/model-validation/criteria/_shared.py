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
# Small helper shared by a handful of criterion modules. Not a criterion
# itself - not picked up by the auto-discovery in __init__.py because its
# filename doesn't start with 'c'.

from __future__ import annotations

from ..samm_model_parser import TTLModel
from ..report import Finding


def element_findings(criterion_id: str, title: str, model: TTLModel, predicate, message_fn, level="FAIL"):
    # Runs `predicate(element)` over every element in the model; wherever
    # it returns a truthy value, turns that into a Finding via `message_fn`.
    findings = []
    for el in model.elements.values():
        msg = predicate(el)
        if msg:
            findings.append(Finding(criterion_id, title, level, model.file, message_fn(el, msg),
                                     element=el.name, line=el.line_no))
    return findings
