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
# Helper around the SAMM CLI jar.
#
# Mirrors the download logic already used in
# ``.github/actions/model-validation/index.js`` and the command set already
# used in ``generate.sh`` (``aspect <file> validate`` / ``aspect <file> to
# schema`` / ``aspect <file> to json``), just ported to Python so the MS2
# criteria that need the CLI (validation, JSON schema vs. example payload)
# can shell out to it too.

from __future__ import annotations

import shutil
import subprocess
import urllib.request
from pathlib import Path

CACHE_DIR = Path(".SAMMCLI")


def ensure_samm_cli(version: str, cache_dir: Path = CACHE_DIR) -> Path | None:
    # Downloads the samm-cli jar (once, cached) or returns None if it
    # could not be obtained (e.g. no network access).
    cache_dir.mkdir(parents=True, exist_ok=True)
    jar_path = cache_dir / f"samm-cli-{version}.jar"

    if jar_path.exists():
        return jar_path

    if shutil.which("java") is None:
        return None

    url = f"https://github.com/eclipse-esmf/esmf-sdk/releases/download/v{version}/samm-cli-{version}.jar"
    try:
        urllib.request.urlretrieve(url, jar_path)
    except OSError:
        return None

    return jar_path if jar_path.exists() else None


def run_samm_cli(jar_path: Path, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    command = ["java", "-Dpolyglot.engine.WarnInterpreterOnly=false", "-jar", str(jar_path), *args]
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)
