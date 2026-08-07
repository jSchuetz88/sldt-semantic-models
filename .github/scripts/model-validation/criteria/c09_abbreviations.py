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
# MS2-09: "use abbreviations only when necessary and if these are
# sufficiently common".
#
# Not a machine-checkable criterion: whether an abbreviation is "necessary"
# and "sufficiently common" is a judgement call that can't be reduced to a
# reliable text pattern without an unavoidably arbitrary allow-list of
# "known-good" abbreviations, which produces more noise than signal.
# Doesn't attempt any analysis; always reports the same static SKIP note
# that this item needs manual review.

from __future__ import annotations

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-09"
TITLE = "Abbreviations used only when necessary and common (not automatically verifiable)"
CATEGORY = "Semantic Quality"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    return [Finding(ID, TITLE, "SKIP", model.file,
                     "checked by reviewer - abbreviation necessity/commonality cannot be automatically verified")]
