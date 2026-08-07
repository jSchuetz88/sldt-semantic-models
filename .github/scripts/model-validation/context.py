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
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import config, samm_cli


@dataclass
class GeneratedArtifacts:
    # Result of one `aspect <file> to schema` / `to json` SAMM CLI round
    # trip for a given model - see Context.generated_artifacts below.
    schema_path: Path | None
    payload_path: Path | None
    error: str | None = None
    # True when generation was deliberately not attempted (no jar, or the
    # model doesn't validate) - as opposed to being attempted and failing.
    # Callers use this to report SKIP instead of FAIL for the former: it's
    # not evidence of anything wrong with *this* criterion's own check.
    skipped: bool = False


@dataclass
class Context:
    repo_root: Path
    base_branch: str
    changed_files: list[str] = field(default_factory=list)
    _samm_jar: Path | None = field(default=None, init=False, repr=False)
    _samm_jar_resolved: bool = field(default=False, init=False, repr=False)
    _generated_artifacts: dict[str, GeneratedArtifacts] = field(default_factory=dict, init=False, repr=False)
    _validation_results: dict[str, subprocess.CompletedProcess] = field(default_factory=dict, init=False, repr=False)

    @property
    def samm_jar(self) -> Path | None:
        # Lazily downloads (once per run) the SAMM CLI jar in the version
        # pinned in config.json (see config.py), used by the criteria
        # that need to actually run the CLI (schema/payload generation, MS2-20).
        if not self._samm_jar_resolved:
            version = config.load_config(self.repo_root).samm_cli_version
            self._samm_jar = samm_cli.ensure_samm_cli(version)
            self._samm_jar_resolved = True
        return self._samm_jar

    def validation_result(self, model) -> subprocess.CompletedProcess | None:
        # Lazily runs (once per model file, cached for the rest of this
        # run) `samm-cli aspect <file> validate`. Shared between MS2-01
        # (which reports it directly) and generated_artifacts() /
        # ms2_check.py's main loop (which skip further work entirely for a
        # model that doesn't even validate - no point generating artifacts
        # from, or checking naming conventions on, a model that's already
        # known to be broken). Returns None if the jar itself is
        # unavailable (caller can't distinguish "not run" from "ran and
        # passed" any other way).
        if model.file in self._validation_results:
            return self._validation_results[model.file]

        jar = self.samm_jar
        if jar is None:
            return None

        result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "validate"])
        self._validation_results[model.file] = result
        return result

    def generated_artifacts(self, model) -> GeneratedArtifacts:
        # Lazily generates (once per model file, cached for the rest of
        # this run) the JSON schema and example JSON payload via the SAMM
        # CLI's `to schema` / `to json` commands. Several criteria want to
        # inspect these (currently MS2-20; a criterion wanting to judge
        # property names on the fully-resolved payload rather than the raw
        # TTL identifiers would too) - sharing this avoids each one
        # shelling out to samm-cli separately for the same file.
        #
        # schema_path/payload_path being None always comes with `error` set;
        # `skipped` tells the caller whether that's because generation was
        # deliberately not attempted (SKIP-worthy) or genuinely failed
        # (FAIL-worthy) - see the `skipped` field's own comment.
        if model.file in self._generated_artifacts:
            return self._generated_artifacts[model.file]

        jar = self.samm_jar
        if jar is None:
            result = GeneratedArtifacts(
                None, None, "SAMM CLI jar unavailable (no Java / no network)", skipped=True)
            self._generated_artifacts[model.file] = result
            return result

        validation = self.validation_result(model)
        if validation is not None and validation.returncode != 0:
            result = GeneratedArtifacts(
                None, None, "model does not validate (see MS2-01) - schema/payload generation skipped",
                skipped=True)
            self._generated_artifacts[model.file] = result
            return result

        out_dir = Path(tempfile.mkdtemp(prefix="ms2-artifacts-"))
        schema_path = out_dir / "schema.json"
        payload_path = out_dir / "payload.json"

        schema_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "schema", "-o", str(schema_path)])
        if schema_result.returncode != 0 or not schema_path.exists():
            result = GeneratedArtifacts(
                None, None, f"JSON schema generation failed: {schema_result.stderr.strip()[:300]}")
            self._generated_artifacts[model.file] = result
            return result

        payload_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "json", "-o", str(payload_path)])
        if payload_result.returncode != 0 or not payload_path.exists():
            result = GeneratedArtifacts(
                schema_path, None, f"example JSON payload generation failed: {payload_result.stderr.strip()[:300]}")
            self._generated_artifacts[model.file] = result
            return result

        result = GeneratedArtifacts(schema_path, payload_path)
        self._generated_artifacts[model.file] = result
        return result

    def get_changed_files(self) -> list[str]:
        # Returns every file changed on this branch compared to base_branch
        # (not just .ttl files - used e.g. by MS2-21 to check whether
        # RELEASE_NOTES.md was also touched). Assumes `git fetch` has
        # already made base_branch available locally (see the checkout
        # step in governance.yml).
        #
        # Three dots, not two: `A...B` diffs against the merge-base of A
        # and B, i.e. "what did this branch change since it forked from
        # base_branch" - independent of whatever else has landed on
        # base_branch since then. `A..B` (two dots) instead diffs directly
        # against base_branch's current tip, which would also pick up
        # unrelated files simply because base_branch moved on without this
        # branch, misattributing them to this PR.
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{self.base_branch}...HEAD"],
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
