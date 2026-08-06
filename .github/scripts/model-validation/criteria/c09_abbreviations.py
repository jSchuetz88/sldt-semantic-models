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
MS2-09: "use abbreviations only when necessary and if these are
sufficiently common".

Deliberately NOT implemented as a check: whether an abbreviation is
"necessary" and "sufficiently common" is a judgement call that can't be
reduced to a reliable text pattern without an unavoidably arbitrary
allow-list of "known-good" abbreviations, which produces more noise than
signal. This file exists only so the criterion still shows up in the
one-file-per-criterion overview; it has no `check` function, so
criteria/__init__.py's auto-discovery skips it. This stays a manual
review item on the PR checklist.
"""
