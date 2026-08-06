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
MS2-13: "name of aspect is singular except if it only has one property
which is a Collection, List or Set. In these cases, the aspect name is
plural."

Only the collection-valued-single-property -> must-be-plural direction is
checked. The reverse (aspect should be singular) is not enforced because
naive endswith('s') plural detection is unreliable for English nouns.
"""

from __future__ import annotations

from ..context import Context
from ..model import TTLModel
from ..report import Finding

TITLE = "Aspect name is singular/plural depending on single Collection property"
COLLECTION_TYPES = {"Collection", "List", "Set", "SortedSet"}


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    aspect = model.aspect
    if not aspect or len(aspect.properties) != 1:
        return []

    prop = model.elements.get(aspect.properties[0])
    if not prop or not prop.characteristic:
        return []

    characteristic = model.elements.get(prop.characteristic)
    if not characteristic or characteristic.short_type not in COLLECTION_TYPES:
        return []

    if not aspect.name.endswith("s"):
        return [Finding("MS2-13", TITLE, "FAIL", model.file,
                         f"aspect '{aspect.name}' has a single Collection/List/Set property "
                         f"('{prop.name}') so its name should be plural", element=aspect.name)]
    return [Finding("MS2-13", TITLE, "INFO", model.file,
                     f"aspect '{aspect.name}' is (heuristically) plural, matching its single "
                     f"collection-valued property", element=aspect.name)]
