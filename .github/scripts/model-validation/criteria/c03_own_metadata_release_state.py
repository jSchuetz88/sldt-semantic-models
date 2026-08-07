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

from __future__ import annotations

import json
from pathlib import Path

from ..context import Context
from ..samm_model_parser import TTLModel
from ..report import Finding

ID = "MS2-03"
TITLE = "metadata.json exists with status 'release'"
CATEGORY = "Formal Requirements"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    if not model.namespace or not model.version:
        return [Finding(ID, TITLE, "FAIL", model.file,
                         "could not determine this model's own namespace/version")]

    meta_path = Path(model.namespace) / model.version / "metadata.json"
    if not meta_path.exists():
        return [Finding(ID, TITLE, "FAIL", model.file, f"{meta_path} does not exist")]

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [Finding(ID, TITLE, "FAIL", model.file, f"{meta_path} is not valid JSON: {e}")]

    if meta.get("status") != "release":
        return [Finding(ID, TITLE, "FAIL", model.file,
                         f"{meta_path} has status '{meta.get('status')}', expected 'release'")]
    return [Finding(ID, TITLE, "INFO", model.file, f"{meta_path} has status 'release'")]
