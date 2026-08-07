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
# MS2-03: "metadata.json exists with status 'release'".
#
# Broadened beyond the letter of that wording: a model's metadata.json
# legitimately moves through - or ends up in - other lifecycle states too
# (e.g. a PR whose whole point is deprecating a model), so any of
# VALID_STATUSES is accepted, not just "release". Still catches real typos
# like "deprecate" (missing the 'd') since those aren't in the set either.

from __future__ import annotations

import json
from pathlib import Path

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-03"
TITLE = "metadata.json exists with a valid status"
CATEGORY = "Formal Requirements"
POST_COMMENT = True
VALID_STATUSES = {"release", "deprecated", "draft", "invalidated"}


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    if not model.namespace or not model.version:
        return [Finding(ID, TITLE, "FAIL", model.file,
                         "could not determine this model's own namespace/version", line=1)]

    meta_path = Path(model.namespace) / model.version / "metadata.json"
    if not meta_path.exists():
        return [Finding(ID, TITLE, "FAIL", model.file, f"{meta_path} does not exist", line=1)]

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [Finding(ID, TITLE, "FAIL", model.file, f"{meta_path} is not valid JSON: {e}", line=1)]

    status = meta.get("status")
    if status not in VALID_STATUSES:
        return [Finding(ID, TITLE, "FAIL", model.file,
                         f"{meta_path} has status '{status}', expected one of {sorted(VALID_STATUSES)}", line=1)]
    return [Finding(ID, TITLE, "INFO", model.file, f"{meta_path} has status '{status}'")]
