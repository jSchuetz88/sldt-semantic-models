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
MS2-18: "all external / imported models have the state 'release'".

Reuses the prefix-parsing / metadata-lookup logic already implemented in
.github/scripts/check-model-states.py (exposed via ctx.check_model_states)
instead of duplicating it.
"""

from __future__ import annotations

from ..context import Context
from ..model import TTLModel
from ..report import Finding

TITLE = "Imported models are in 'release' state"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    cms = ctx.check_model_states
    findings = []
    for prefix_info in cms.parse_prefixes(model.file):
        folder, version = prefix_info["folder"], prefix_info["version"]
        if folder == model.namespace and version == model.version:
            continue  # this is the model's own namespace, see MS2-19
        meta = cms.check_metadata(folder, version)
        if not meta:
            findings.append(Finding("MS2-18", TITLE, "FAIL", model.file,
                                     f"metadata.json not found for imported model {folder}:{version}"))
        elif meta.get("status") != "release":
            findings.append(Finding("MS2-18", TITLE, "FAIL", model.file,
                                     f"imported model {folder}:{version} has status "
                                     f"'{meta.get('status')}', expected 'release'"))
    if not findings:
        findings.append(Finding("MS2-18", TITLE, "INFO", model.file,
                                 "all imported/external models are in 'release' state"))
    return findings
