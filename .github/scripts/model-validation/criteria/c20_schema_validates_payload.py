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
MS2-20: "generated json schema validates against example json payload".

Uses the SAMM CLI's `aspect <file> to schema` / `aspect <file> to json`
commands (same ones as generate.sh) to produce both artifacts, then
cross-validates them with the `jsonschema` package if it's installed.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .. import samm_cli
from ..context import Context
from ..model import TTLModel
from ..report import Finding

TITLE = "Generated JSON schema validates against generated example payload"


def check(model: TTLModel, ctx: Context) -> list[Finding]:
    jar = ctx.samm_jar
    if jar is None:
        return [Finding("MS2-20", TITLE, "SKIP", model.file,
                         "SAMM CLI jar unavailable (no Java / no network) - run "
                         "`java -jar samm-cli-<version>.jar aspect <file> to schema` / `to json` manually")]

    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.json"
        payload_path = Path(tmp) / "payload.json"

        schema_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "schema", "-o", str(schema_path)])
        if schema_result.returncode != 0 or not schema_path.exists():
            return [Finding("MS2-20", TITLE, "FAIL", model.file,
                             f"JSON schema generation failed: {schema_result.stderr.strip()[:300]}")]

        payload_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "json", "-o", str(payload_path)])
        if payload_result.returncode != 0 or not payload_path.exists():
            return [Finding("MS2-20", TITLE, "FAIL", model.file,
                             f"example JSON payload generation failed: {payload_result.stderr.strip()[:300]}")]

        try:
            import jsonschema
        except ImportError:
            return [Finding("MS2-20", TITLE, "SKIP", model.file,
                             "schema and example payload generated successfully, but the "
                             "'jsonschema' package is not installed so they were not cross-validated "
                             "(pip install jsonschema)")]

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(payload, schema)
        except jsonschema.ValidationError as e:
            return [Finding("MS2-20", TITLE, "FAIL", model.file,
                             f"generated example payload does not validate against the generated "
                             f"JSON schema: {e.message}")]

    return [Finding("MS2-20", TITLE, "INFO", model.file,
                     "generated JSON schema validates against the generated example payload")]
