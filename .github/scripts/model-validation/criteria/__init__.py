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
# One file per MS2 checklist item from PULL_REQUEST_TEMPLATE.md, named
# `cNN_<slug>.py` (NN = the checklist item number). Each such module
# exposes:
#
# - ``ID``: the criterion id, e.g. "MS2-02"
# - ``TITLE``: a short human-readable title
# - ``CATEGORY``: one of "Model Validation" / "Formal Requirements" /
#   "Semantic Quality" - used to group the report table into sections
# - ``check(model, ctx) -> list[Finding]``: the sub-routine itself
#
# It receives the data package the master script (``ms2_check.py``) built
# for the changed ``.ttl`` file (see ``samm_model_parser.py``) plus the shared
# ``Context`` (see ``context.py``). Nothing in here talks to the list of
# changed files, GitHub, or the per-criterion config (see ``config.py``)
# directly - that's the master's job.
#
# Not every MS2 criterion can be verified with certainty from the file
# content alone. Criteria that are only heuristically checkable report at
# WARN level instead of FAIL, and say so, rather than pretending to be an
# authoritative check; criteria that can't render a verdict at all (e.g.
# "abbreviations only when necessary" is a pure judgement call - see
# c09_abbreviations.py) still have a `check` function, but it always
# reports the same static SKIP/NOTE regardless of file content, rather
# than pretending to analyze something unanalyzable. FAIL is reserved for
# criteria that are genuinely unambiguous from the text - and even those
# can be downgraded to non-blocking per-repo via config.json
# (see config.py) if a team decides a given MUST shouldn't break CI yet.
#
# REGISTRY below is built automatically by importing every cNN_*.py module
# in this folder (in numeric order) and collecting its ID/TITLE/CATEGORY/
# check. To add a new criterion: drop in a new cNN_<slug>.py file with an
# ID, TITLE, CATEGORY and check function - no need to touch this file. A criterion that
# is intentionally not machine-answerable still needs a `check` function
# (returning a constant SKIP/NOTE Finding, see c09/c13) to show up in
# REGISTRY and thus in the report at all; a cNN_*.py file with no `check`
# function whatsoever is excluded from REGISTRY entirely (not currently
# used by any criterion here, but supported for a future one that
# shouldn't appear in the automated report at all).

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..samm_model_parser import TTLModel
from ..context import Context
from ..report import Finding

_PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Criterion:
    id: str
    title: str
    category: str
    check: Callable[[TTLModel, Context], list[Finding]]


def _discover_registry() -> list[Criterion]:
    registry = []
    modules = sorted(
        (m for m in pkgutil.iter_modules([str(_PACKAGE_DIR)]) if m.name[:1] == "c"),
        key=lambda m: m.name,
    )
    for module_info in modules:
        module = importlib.import_module(f"{__name__}.{module_info.name}")
        check_fn = getattr(module, "check", None)
        if check_fn is not None:
            registry.append(Criterion(id=module.ID, title=module.TITLE, category=module.CATEGORY, check=check_fn))
    return registry


REGISTRY = _discover_registry()
