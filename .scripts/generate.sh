#!/bin/bash
#######################################################################
# Copyright (c) 2023 Robert Bosch Manufacturing Solutions GmbH
# Copyright (c) 2026 Catena-X Automotive Network e.V.
# Copyright (c) 2023 Contributors to the Eclipse Foundation
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


# REMARKS:
# ========
# This script generates a set of artifacts for a given SAMM model in a ttl-file.
# Preconditiions:
# -internet connection to download specified SAMM CLI provided in $SAMMCLI folder and Catena-X CSS style

# Usage (always run from the repository root, e.g. as bash ./.scripts/generate.sh
# - the .SAMMCLI/ cache and every model path are resolved relative to the
# current working directory, not to this script's own location):
# Apply script to a single file
# bash ./.scripts/generate.sh io.catenax.vehicle.product_description/2.0.0/ProductDescription.ttl
# To generate files for all models in repo
# find ./ -type f -name "*.ttl" -exec bash ./.scripts/generate.sh "{}" \;

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

# SAMM CLI version comes from .github/src/config.json - the same file
# quality_gate/config.py reads for the MS2 criteria check - so this
# can't silently drift from what CI validates models against.
CONFIG=.github/src/config.json
SAMMFOLDER=.SAMMCLI
CATENAXCSS=$SAMMFOLDER/catena-template.css
CATENAXCUSTOMCSSURL=https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-hub/main/backend/src/main/resources/catena-template.css

# samm-cli 2.16.0's class files require JDK 25 to even load, and on JDK 25
# it triggers two harmless-but-noisy JVM warnings on every invocation: one
# from a native library load (jansi) that newer JDKs warn about by
# default, one from a terminally-deprecated sun.misc.Unsafe call inside
# its GraalVM/Truffle internals. Both have a dedicated suppression flag,
# but only on JDK 23+ - moot here since this jar won't run on anything
# older anyway.
JAVA_FLAGS="--enable-native-access=ALL-UNNAMED --sun-misc-unsafe-memory-access=allow"

# Artifact types to generate: CLI command, file ending, CLI options
commands=(aas aas schema json openapi html parquet)
endings=(-aas.xml .aasx -schema.json .json .yml .html .parquet)
toggles=("-f xml" "-f aasx" "" "" "-b=catenax.io" "-c $CATENAXCSS")

# Filled by generate_artefacts, read by create_report
generated=0
report=()

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

# Print a value from the settings in config.json, fail if it is missing
read_setting() {
  local value
  value="$(jq -r ".settings.$1" "$CONFIG" 2>/dev/null)"
  if [ -z "$value" ] || [ "$value" = "null" ]; then
    echo "Could not read settings.$1 from $CONFIG" >&2
    return 1
  fi
  echo "$value"
}

samm() {
  java $JAVA_FLAGS -jar "$SAMMCLI" aspect "$@"
}

# Download SAMM CLI and stylesheet if needed and verify the CLI's checksum
prepare_samm_cli() {
  SAMM_CLI_VERSION="$(read_setting samm_cli_version)" || return 1
  SAMM_CLI_SHA256="$(read_setting samm_cli_sha256)" || return 1
  local jarname="samm-cli-$SAMM_CLI_VERSION.jar"
  local url="https://github.com/eclipse-esmf/esmf-sdk/releases/download/v$SAMM_CLI_VERSION/$jarname"
  SAMMCLI="$SAMMFOLDER/$jarname"
  mkdir -p "$SAMMFOLDER"

  echo "Check availability of SAMM CLI"
  if [ ! -f "$SAMMCLI" ]; then
    echo "$SAMMCLI does not exist. Will download"
    curl -fL -o "$SAMMCLI" "$url"
  fi

  # Verify the SAMM CLI jar against the SHA-256 in config.json.
  local actual
  actual="$(shasum -a 256 "$SAMMCLI" | cut -d' ' -f1)"
  if [ "$actual" != "$SAMM_CLI_SHA256" ]; then
    echo "SHA-256 of $SAMMCLI ($actual) does not match $SAMM_CLI_SHA256 from $CONFIG" >&2
    return 1
  fi

  if [ ! -f "$CATENAXCSS" ]; then
    echo "$CATENAXCSS does not exist. Will download"
    curl -fL -o "$CATENAXCSS" "$CATENAXCUSTOMCSSURL"
  fi
  return 0
}

validate_model() {
  echo "Validate $MODEL with SAMM CLI"
  if ! samm "$MODEL" validate; then
    echo "$MODEL does not validate - skipping artifact generation" >&2
    return 1
  fi
}

# A model can validate but still fail to generate one of the artifact
# types (SAMM CLI bug/limitation for that particular structure). That's
# not fatal: keep whichever artifact types succeeded, warn on whichever
# didn't (removing any partial/corrupt output that type's failed attempt
# may have left behind), and still return 0 - a caller should commit the
# artifacts that could be built rather than getting none of them over one
# format that can't.
generate_artefacts() {
  local i out rc message log
  log="$(mktemp)"

  echo "Generate artifacts for $MODEL"
  for i in "${!commands[@]}"; do
    out="$GENDIR/$MODELNAME${endings[$i]}"
    echo "generate ${commands[$i]} into $out"

    rc=0
    # toggles are intentionally unquoted: they hold several CLI options
    samm "$MODEL" to ${commands[$i]} ${toggles[$i]} -o "$out" > "$log" 2>&1 || rc=$?
    cat "$log"

    if [ "$rc" -eq 0 ]; then
      generated=$((generated + 1))
      report+=("| ✅ | \`$(basename "$out")\` | |")
    else
      echo "::warning::could not generate '${commands[$i]}' artifact for $MODEL ($out) - skipping" >&2
      rm -f "$out"
      message="$(to_cell "$log")"
      report+=("| ❌ | \`$(basename "$out")\` | ${message:-unknown (exit code $rc)} |")
    fi
  done

  rm -f "$log"
}

# Turn CLI output into a single markdown table cell
to_cell() {
  sed $'s/\x1b\\[[0-9;]*m//g' "$1" | tr -d '\r' | grep -vE '^[[:space:]]*$|^WARNING: ' | cut -c1-300 | head -n 5 \
    | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/|/\&#124;/g' \
    | awk 'NR>1{printf "<br>"} {printf "%s", $0}'
}

# Record when and with which SAMM CLI version the artifacts were built, and
# the result per artifact. Only reached for models that validate, and only
# written if at least one artifact was generated - if a later run fails,
# the README keeps describing the artifacts still in this folder.
create_report() {
  [ "$generated" -gt 0 ] || return 0
  {
    echo "# Report"
    echo
    echo "This was validated and generated at $(date -u '+%d.%m.%Y') with SAMM CLI $SAMM_CLI_VERSION."
    echo
    echo "| | Artifact | Message |"
    echo "|---|---|---|"
    printf '%s\n' "${report[@]}"
  } > "$GENDIR/README.md"
}

main() {
  MODEL="$1"
  MODELNAME="$(basename "$MODEL" .ttl)"
  GENDIR="$(dirname "$MODEL")/gen"

  prepare_samm_cli || exit 1
  validate_model || exit 1
  generate_artefacts
  create_report
}

main "$@"
