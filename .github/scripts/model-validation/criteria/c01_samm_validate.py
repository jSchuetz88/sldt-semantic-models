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
MS2-01: "the model validates with the SAMM SDS SDK in the version
specified in the Readme.md of this repository by the time of the MS2
check".
"""

from __future__ import annotations

from .. import samm_cli
from ..context import Context
from ..model import TTLModel
from ..report import Finding

ID = "MS2-01"
TITLE = "Model validates with SAMM CLI"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    jar = ctx.samm_jar
    if jar is None:
        return [Finding("MS2-01", TITLE, "SKIP", model.file,
                         "SAMM CLI jar unavailable (no Java / no network) - run "
                         "`java -jar samm-cli-<version>.jar aspect <file> validate` manually")]

    result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "validate"])
    if result.returncode != 0:
        detail = (result.stdout or result.stderr or "").strip().splitlines()
        first_line = detail[0] if detail else f"exit code {result.returncode}"
        return [Finding("MS2-01", TITLE, "FAIL", model.file, f"samm-cli validation failed: {first_line}")]
    return [Finding("MS2-01", TITLE, "INFO", model.file, "samm-cli validation passed")]
