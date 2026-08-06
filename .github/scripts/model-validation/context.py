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
# The Context object is created once by the master script and handed to
# every criterion sub-routine together with the parsed model. It bundles
# everything that is shared across criteria (repo root, list of changed
# files, a lazily-downloaded SAMM CLI jar, git plumbing, ...) so individual
# criteria stay small and don't each re-implement this bookkeeping.

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import samm_cli


@dataclass
class Context:
    repo_root: Path
    base_branch: str
    changed_files: list[str] = field(default_factory=list)
    _samm_jar: Path | None = field(default=None, init=False, repr=False)
    _samm_jar_resolved: bool = field(default=False, init=False, repr=False)

    @property
    def samm_jar(self) -> Path | None:
        # Lazily downloads (once per run) the SAMM CLI jar in the version
        # pinned in README.md, used by the criteria that need to actually
        # run the CLI (schema/payload generation, MS2-20).
        if not self._samm_jar_resolved:
            version = samm_cli.samm_version_from_readme(self.repo_root)
            self._samm_jar = samm_cli.ensure_samm_cli(version)
            self._samm_jar_resolved = True
        return self._samm_jar

    def get_changed_files(self) -> list[str]:
        # Returns every file changed on this branch compared to base_branch
        # (not just .ttl files - used e.g. by MS2-21 to check whether
        # RELEASE_NOTES.md was also touched). Assumes `git fetch` has
        # already made base_branch available locally (see the checkout
        # step in governance.yml).
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{self.base_branch}..HEAD"],
                capture_output=True, text=True, check=True,
            )
        except subprocess.CalledProcessError as e:
            # stderr, not stdout: --list-changed-files relies on stdout being
            # clean JSON for the workflow to parse.
            print(f"Error running git diff: {e}", file=sys.stderr)
            return []
        return result.stdout.splitlines()

    def get_changed_ttl_files(self) -> list[str]:
        return [f for f in self.get_changed_files() if f.endswith(".ttl")]
