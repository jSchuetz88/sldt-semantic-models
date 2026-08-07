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
# MS2-07: "all contributors to this model are mentioned in copyright header
# of model file".
#
# Only checks that a copyright header block is present at the top of the
# file. Verifying that it actually names *every* contributor isn't
# reliably automatable (git authorship is GitHub account names, headers
# name companies/organizations - the two don't map 1:1), so that part is
# left to the reviewer.

from __future__ import annotations

import re

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-07"
TITLE = "Copyright header exists"
CATEGORY = "Formal Requirements"
POST_COMMENT = True
COPYRIGHT_LINE_RE = re.compile(r"#\s*Copyright\s*\(?c\)?\s+\d{4}\s+(.+?)\s*$", re.MULTILINE)


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    header_match = re.match(r"(?:#.*\n)+", model.text)
    header = header_match.group(0) if header_match else ""
    copyright_holders = COPYRIGHT_LINE_RE.findall(header)

    if not copyright_holders:
        return [Finding(ID, TITLE, "FAIL", model.file,
                         "no copyright header found at the top of the file", line=1)]
    return [Finding(ID, TITLE, "INFO", model.file,
                     f"copyright header present, lists: {copyright_holders}")]
