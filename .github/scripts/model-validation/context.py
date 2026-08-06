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
The Context object is created once by the master script and handed to
every criterion sub-routine together with the parsed model. It bundles
everything that is shared across criteria (repo root, list of changed
files, a lazily-downloaded SAMM CLI jar, ...) so individual criteria stay
small and don't each re-implement this bookkeeping.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import git_utils, samm_cli


@dataclass
class Context:
    repo_root: Path
    base_branch: str
    changed_files: list[str] = field(default_factory=list)
    _samm_jar: Path | None = field(default=None, init=False, repr=False)
    _samm_jar_resolved: bool = field(default=False, init=False, repr=False)

    @property
    def samm_jar(self) -> Path | None:
        """Lazily downloads (once per run) the SAMM CLI jar in the version
        pinned in README.md, used by the criteria that need to actually
        run the CLI (schema/payload generation, MS2-20)."""
        if not self._samm_jar_resolved:
            version = samm_cli.samm_version_from_readme(self.repo_root)
            self._samm_jar = samm_cli.ensure_samm_cli(version)
            self._samm_jar_resolved = True
        return self._samm_jar

    def get_changed_ttl_files(self) -> list[str]:
        return git_utils.get_changed_ttl_files(self.base_branch)

    def commit_authors(self, file_path: str) -> list[str]:
        """Names of the git authors who touched `file_path` on this branch
        since it diverged from base_branch. Used as a hint for the
        (not reliably automatable) copyright/contributor criterion."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%an", f"{self.base_branch}..HEAD", "--", file_path],
                capture_output=True, text=True, check=True,
            )
        except subprocess.CalledProcessError:
            return []
        names = [n.strip() for n in result.stdout.splitlines() if n.strip()]
        # de-duplicate while preserving order
        seen: set[str] = set()
        unique = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique
