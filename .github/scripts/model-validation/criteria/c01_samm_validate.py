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

Deliberately NOT implemented as a check here: the `validate-model-proposal`
job in .github/workflows/governance.yml already runs this exact
validation via .github/actions/model-validation for every changed .ttl
file. Re-running samm-cli validate a second time from this script (and
downloading a second copy of the jar) would just duplicate that job's
work without adding anything. This file exists only so the criterion
still shows up in the one-file-per-criterion overview; it has no `check`
function, so criteria/__init__.py's auto-discovery skips it.
"""
