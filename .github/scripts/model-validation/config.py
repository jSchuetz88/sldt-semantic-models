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
# Loads ms2-criteria.json (in this same directory), the per-repo overrides
# for the MS2 criteria. Two independent knobs per criterion (both default
# to "on"):
#
# "enabled":  false -> the criterion is skipped entirely, no Findings at all
# "blocking": false -> the criterion still runs and is reported, but any
# FAIL it produces is downgraded to WARN, so it no
# longer breaks the CI job (still a MUST per the PR
# template, just not (yet) enforced automatically)
#
# Example ms2-criteria.json:
#
# {
# "MS2-19": {"blocking": false},
# "MS2-14": {"enabled": false}
# }
#
# A criterion not mentioned in the file, or the file not existing at all
# (it's fine to delete it - an empty/missing file just means no overrides),
# behaves exactly as if this module didn't exist (enabled + blocking).
# Criterion ids are "MS2-01" through "MS2-22", matching the checklist order
# in PULL_REQUEST_TEMPLATE.md.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_RELPATH = ".github/scripts/model-validation/ms2-criteria.json"


@dataclass(frozen=True)
class CriterionOverride:
    enabled: bool = True
    blocking: bool = True


@dataclass
class Config:
    overrides: dict[str, CriterionOverride] = field(default_factory=dict)

    def for_criterion(self, criterion_id: str) -> CriterionOverride:
        return self.overrides.get(criterion_id, CriterionOverride())

    def is_enabled(self, criterion_id: str) -> bool:
        return self.for_criterion(criterion_id).enabled

    def is_blocking(self, criterion_id: str) -> bool:
        return self.for_criterion(criterion_id).blocking


def load_config(repo_root: Path, path: str = DEFAULT_CONFIG_RELPATH) -> Config:
    config_path = repo_root / path
    if not config_path.exists():
        return Config()

    raw = json.loads(config_path.read_text(encoding="utf-8")) or {}
    overrides = {}
    for criterion_id, settings in raw.items():
        settings = settings or {}
        overrides[criterion_id] = CriterionOverride(
            enabled=bool(settings.get("enabled", True)),
            blocking=bool(settings.get("blocking", True)),
        )
    return Config(overrides)
