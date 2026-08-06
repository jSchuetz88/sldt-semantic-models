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
"""Small git plumbing shared by the master script and Context."""

from __future__ import annotations

import subprocess


def get_changed_ttl_files(base_branch: str = "origin/main") -> list[str]:
    """Returns the .ttl files changed on this branch compared to
    `base_branch`. Assumes `git fetch` has already made `base_branch`
    available locally (see the checkout step in governance.yml)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}..HEAD"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}")
        return []
    return [f for f in result.stdout.splitlines() if f.endswith(".ttl")]
