
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
One sub-routine per MS2 checklist item from PULL_REQUEST_TEMPLATE.md.

Every ``check_xx(model, ctx)`` function receives the data package the
master script (``ms2_check.py``) built for the changed ``.ttl`` file (see
``model.py``) plus the shared ``Context`` (see ``context.py``), and
returns a list of ``Finding``. Nothing here talks to the filesystem list
of changed files or GitHub directly - that's the master's job.

Not every MS2 criterion can be verified with certainty from the file
content alone (e.g. "abbreviations only when necessary" is a judgement
call). Those criteria are still implemented as best-effort heuristics,
but report at WARN/INFO level instead of FAIL, and say so, rather than
pretending to be an authoritative check. FAIL is reserved for criteria
that are genuinely unambiguous from the text.

To add a new / changed criterion: write a ``check_xx`` function and add
it to the ``REGISTRY`` at the bottom of this file.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from .context import Context
from .model import TTLModel
from .report import Finding
from . import samm_cli

CAMEL_CASE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def _element_findings(criterion_id: str, title: str, model: TTLModel, predicate, message_fn, level="FAIL"):
    findings = []
    for el in model.elements.values():
        msg = predicate(el)
        if msg:
            findings.append(Finding(criterion_id, title, level, model.file, message_fn(el, msg), element=el.name))
    return findings


# --- MS2-01 -----------------------------------------------------------
# "the model validates with the SAMM SDS SDK in the version specified in
# the Readme.md of this repository"
def check_01_samm_validate(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Model validates with SAMM CLI"
    jar = ctx.samm_jar
    if jar is None:
        return [Finding("MS2-01", title, "SKIP", model.file,
                         "SAMM CLI jar unavailable (no Java / no network) - run "
                         "`java -jar samm-cli-<version>.jar aspect <file> validate` manually")]

    result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "validate"])
    if result.returncode != 0:
        detail = (result.stdout or result.stderr or "").strip().splitlines()
        first_line = detail[0] if detail else f"exit code {result.returncode}"
        return [Finding("MS2-01", title, "FAIL", model.file, f"samm-cli validation failed: {first_line}")]
    return [Finding("MS2-01", title, "INFO", model.file, "samm-cli validation passed")]


# --- MS2-02 -------------------------------------------------------------
# "use Camel-Case"
def check_02_camel_case(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Identifiers use Camel-Case"

    def bad(el):
        return None if CAMEL_CASE_RE.match(el.name) else "contains characters other than letters/digits"

    return _element_findings("MS2-02", title, model, bad,
                              lambda el, msg: f"identifier '{el.name}' is not Camel-Case ({msg})")


# --- MS2-03 ---------------------------------------------------------------
# "payload names and property identifiers must not contain two consecutive
# underscores"
def check_03_no_double_underscore(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "No double underscores in identifiers/payload names"
    findings = []
    for el in model.elements.values():
        if "__" in el.name:
            findings.append(Finding("MS2-03", title, "FAIL", model.file,
                                     f"identifier '{el.name}' contains '__'", element=el.name))
        if el.payload_name and "__" in el.payload_name:
            findings.append(Finding("MS2-03", title, "FAIL", model.file,
                                     f"payloadName '{el.payload_name}' contains '__'", element=el.name))
    return findings


# --- MS2-04 / MS2-05 ------------------------------------------------------
# "identifiers for all model elements start with a capital letter except
# for properties" / "the identifier for properties starts with a small
# letter"
def check_04_capitalized_elements(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Non-property identifiers start with a capital letter"

    def bad(el):
        if el.short_type == "Property" or not el.name:
            return None
        return None if el.name[0].isupper() else "does not start with a capital letter"

    return _element_findings("MS2-04", title, model, bad,
                              lambda el, msg: f"'{el.name}' ({el.short_type}) {msg}")


def check_05_lowercase_properties(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Property identifiers start with a lowercase letter"

    def bad(el):
        if el.short_type != "Property" or not el.name:
            return None
        return None if el.name[0].islower() else "does not start with a lowercase letter"

    return _element_findings("MS2-05", title, model, bad,
                              lambda el, msg: f"property '{el.name}' {msg}")


# --- MS2-06 -----------------------------------------------------------
# "all model elements at least contain the fields 'preferred name' and
# 'description' in English language"
def check_06_preferred_name_and_description(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "preferredName and description present (English)"
    findings = []
    for el in model.elements.values():
        if el.preferred_name("en") is None:
            findings.append(Finding("MS2-06", title, "FAIL", model.file,
                                     f"'{el.name}' is missing samm:preferredName ... @en", element=el.name))
        if el.description("en") is None:
            findings.append(Finding("MS2-06", title, "FAIL", model.file,
                                     f"'{el.name}' is missing samm:description ... @en", element=el.name))
    return findings


# --- MS2-07 ------------------------------------------------------------
# "Property and the referenced Characteristic should not have the same
# name"
def check_07_property_characteristic_name_conflict(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Property and its Characteristic have different names"
    findings = []
    for el in model.elements.values():
        if el.short_type == "Property" and el.characteristic and el.characteristic == el.name:
            findings.append(Finding("MS2-07", title, "FAIL", model.file,
                                     f"property '{el.name}' and its characteristic share the same name",
                                     element=el.name))
    return findings


# --- MS2-08 -----------------------------------------------------------
# "the versioning in the URN follows semantic versioning"
def check_08_semver_urn(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "URN version follows semantic versioning"
    findings = []
    if model.version is None:
        findings.append(Finding("MS2-08", title, "FAIL", model.file,
                                 "could not find a base ':' prefix of the form "
                                 "<urn:samm:<namespace>:<MAJOR.MINOR.PATCH>#>"))
        return findings

    path_parts = Path(model.file).parts
    version_dirs = [p for p in path_parts if re.fullmatch(r"\d+\.\d+\.\d+", p)]
    if version_dirs and version_dirs[0] != model.version:
        findings.append(Finding("MS2-08", title, "FAIL", model.file,
                                 f"URN version '{model.version}' does not match the "
                                 f"version folder '{version_dirs[0]}'"))
    if not findings:
        findings.append(Finding("MS2-08", title, "INFO", model.file,
                                 f"URN version '{model.version}' is well-formed and matches its folder"))
    return findings


# --- MS2-09 ---------------------------------------------------------------
# "use abbreviations only when necessary and if these are sufficiently
# common"
#
# Deliberately not implemented: whether an abbreviation is "necessary" and
# "sufficiently common" is a judgement call that can't be reduced to a
# reliable text pattern without an unavoidably arbitrary allow-list. Keep
# this a manual review item on the PR checklist instead of a sub-routine.


# --- MS2-10 (heuristic) --------------------------------------------------
# "avoid redundant prefixes in property names"
def _split_camel(name: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)]


def check_10_redundant_prefixes(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Avoid redundant prefixes in property names (heuristic, needs human review)"
    findings = []
    for el in model.elements.values():
        if el.short_type not in ("Aspect", "Entity") or len(el.properties) < 2:
            continue
        first_words: dict[str, list[str]] = {}
        for prop_name in el.properties:
            words = _split_camel(prop_name)
            if not words:
                continue
            first_words.setdefault(words[0], []).append(prop_name)
        for word, props in first_words.items():
            if len(props) >= 2:
                findings.append(Finding(
                    "MS2-10", title, "WARN", model.file,
                    f"properties {props} of '{el.name}' all share the prefix '{word}' - "
                    f"consider an enclosing Entity instead (e.g. '{word}' with sub-properties)",
                    element=el.name,
                ))
    return findings


# --- MS2-11 --------------------------------------------------------------
# "fields preferredName and description are not the same"
def check_11_preferred_name_not_equal_description(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "preferredName and description are not identical"
    findings = []
    for el in model.elements.values():
        pn = el.preferred_name("en")
        de = el.description("en")
        if pn is not None and pn == de:
            findings.append(Finding("MS2-11", title, "FAIL", model.file,
                                     f"'{el.name}': preferredName and description are identical",
                                     element=el.name))
    return findings


# --- MS2-12 --------------------------------------------------------------
# "preferredName should be human readable and follow normal orthography"
CAMEL_HUMP_RE = re.compile(r"[a-z][A-Z]")


def check_12_preferred_name_readable(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "preferredName is human-readable (not Camel-Case)"
    findings = []
    for el in model.elements.values():
        pn = el.preferred_name("en")
        if pn and " " not in pn and CAMEL_HUMP_RE.search(pn):
            findings.append(Finding("MS2-12", title, "FAIL", model.file,
                                     f"preferredName '{pn}' of '{el.name}' looks Camel-Case, "
                                     f"expected normal word separation",
                                     element=el.name))
    return findings


# --- MS2-13 --------------------------------------------------------------
# "name of aspect is singular except if it only has one property which is
# a Collection, List or Set. In these cases the aspect name is plural."
COLLECTION_TYPES = {"Collection", "List", "Set", "SortedSet"}


def check_13_aspect_singular_plural(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Aspect name is singular/plural depending on single Collection property"
    aspect = model.aspect
    if not aspect or len(aspect.properties) != 1:
        return []

    prop = model.elements.get(aspect.properties[0])
    if not prop or not prop.characteristic:
        return []

    characteristic = model.elements.get(prop.characteristic)
    if not characteristic or characteristic.short_type not in COLLECTION_TYPES:
        return []

    if not aspect.name.endswith("s"):
        return [Finding("MS2-13", title, "FAIL", model.file,
                         f"aspect '{aspect.name}' has a single Collection/List/Set property "
                         f"('{prop.name}') so its name should be plural", element=aspect.name)]
    return [Finding("MS2-13", title, "INFO", model.file,
                     f"aspect '{aspect.name}' is (heuristically) plural, matching its single "
                     f"collection-valued property", element=aspect.name)]


# --- MS2-14 (heuristic) ---------------------------------------------------
# "units are referenced from the SAMM unit catalog whenever possible"
def check_14_units_from_catalog(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Units reference the SAMM unit catalog (heuristic, needs human review)"
    findings = []
    for el in model.elements.values():
        if el.unit and not el.unit.startswith("unit:"):
            findings.append(Finding("MS2-14", title, "WARN", model.file,
                                     f"'{el.name}' uses unit '{el.unit}' which is not from the "
                                     f"'unit:' catalog prefix - confirm no catalog unit fits",
                                     element=el.name))
        if el.short_type == "Unit":
            findings.append(Finding("MS2-14", title, "WARN", model.file,
                                     f"'{el.name}' defines a custom samm:Unit - confirm it does not "
                                     f"already exist in the SAMM unit catalog", element=el.name))
    return findings


# --- MS2-15 (informational) -----------------------------------------------
# "use constraints to make known constraints from the use case explicit"
def check_15_constraints_used(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Constraints used where applicable (informational, needs human review)"
    constrained = [el.name for el in model.elements.values() if el.short_type.endswith("Constraint")]
    if constrained:
        return [Finding("MS2-15", title, "INFO", model.file,
                         f"{len(constrained)} constraint(s) defined: {constrained}")]
    return [Finding("MS2-15", title, "INFO", model.file,
                     "no samm-c constraints found - if the use case has known constraints "
                     "(ranges, patterns, lengths, ...), consider making them explicit")]


# --- MS2-16 (informational) -----------------------------------------------
# "when relying on external standards, they are referenced through a 'see'
# element"
def check_16_external_standards_see(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "External standards referenced via samm:see (informational, needs human review)"
    with_see = [el.name for el in model.elements.values() if el.see]
    if with_see:
        return [Finding("MS2-16", title, "INFO", model.file,
                         f"{len(with_see)} element(s) carry a samm:see reference: {with_see}")]
    return [Finding("MS2-16", title, "INFO", model.file,
                     "no samm:see references found - if this model implements/relates to an "
                     "external standard, reference it via samm:see")]


# --- MS2-17 -----------------------------------------------------------
# "all properties with a simple type have an example value"
def check_17_example_values(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Properties with simple (xsd) type have an example value"
    findings = []
    for el in model.elements.values():
        if el.short_type != "Property" or not el.characteristic:
            continue
        characteristic = model.elements.get(el.characteristic)
        if not characteristic or not characteristic.data_type:
            continue  # characteristic defined elsewhere / not resolvable locally
        if not characteristic.data_type.startswith("xsd:"):
            continue  # complex (Entity) type, not a "simple type"
        if not characteristic.has_example_value:
            findings.append(Finding(
                "MS2-17", title, "FAIL", model.file,
                f"property '{el.name}' -> characteristic '{characteristic.name}' has simple type "
                f"'{characteristic.data_type}' but no samm:exampleValue", element=el.name,
            ))
    return findings


# --- MS2-18 --------------------------------------------------------------
# "all external / imported models have the state 'release'"
def check_18_imported_models_release_state(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Imported models are in 'release' state"
    cms = ctx.check_model_states
    findings = []
    for prefix_info in cms.parse_prefixes(model.file):
        folder, version = prefix_info["folder"], prefix_info["version"]
        if folder == model.namespace and version == model.version:
            continue  # this is the model's own namespace, see MS2-19
        meta = cms.check_metadata(folder, version)
        if not meta:
            findings.append(Finding("MS2-18", title, "FAIL", model.file,
                                     f"metadata.json not found for imported model {folder}:{version}"))
        elif meta.get("status") != "release":
            findings.append(Finding("MS2-18", title, "FAIL", model.file,
                                     f"imported model {folder}:{version} has status "
                                     f"'{meta.get('status')}', expected 'release'"))
    if not findings:
        findings.append(Finding("MS2-18", title, "INFO", model.file,
                                 "all imported/external models are in 'release' state"))
    return findings


# --- MS2-19 -----------------------------------------------------------
# "metadata.json exists with status 'release'"
def check_19_own_metadata_release_state(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "metadata.json exists with status 'release'"
    if not model.namespace or not model.version:
        return [Finding("MS2-19", title, "FAIL", model.file,
                         "could not determine this model's own namespace/version")]

    meta_path = Path(model.namespace) / model.version / "metadata.json"
    if not meta_path.exists():
        return [Finding("MS2-19", title, "FAIL", model.file, f"{meta_path} does not exist")]

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [Finding("MS2-19", title, "FAIL", model.file, f"{meta_path} is not valid JSON: {e}")]

    if meta.get("status") != "release":
        return [Finding("MS2-19", title, "FAIL", model.file,
                         f"{meta_path} has status '{meta.get('status')}', expected 'release'")]
    return [Finding("MS2-19", title, "INFO", model.file, f"{meta_path} has status 'release'")]


# --- MS2-20 -----------------------------------------------------------
# "generated json schema validates against example json payload"
def check_20_schema_validates_payload(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Generated JSON schema validates against generated example payload"
    jar = ctx.samm_jar
    if jar is None:
        return [Finding("MS2-20", title, "SKIP", model.file,
                         "SAMM CLI jar unavailable (no Java / no network) - run "
                         "`java -jar samm-cli-<version>.jar aspect <file> to schema` / `to json` manually")]

    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.json"
        payload_path = Path(tmp) / "payload.json"

        schema_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "schema", "-o", str(schema_path)])
        if schema_result.returncode != 0 or not schema_path.exists():
            return [Finding("MS2-20", title, "FAIL", model.file,
                             f"JSON schema generation failed: {schema_result.stderr.strip()[:300]}")]

        payload_result = samm_cli.run_samm_cli(jar, ["aspect", model.file, "to", "json", "-o", str(payload_path)])
        if payload_result.returncode != 0 or not payload_path.exists():
            return [Finding("MS2-20", title, "FAIL", model.file,
                             f"example JSON payload generation failed: {payload_result.stderr.strip()[:300]}")]

        try:
            import jsonschema
        except ImportError:
            return [Finding("MS2-20", title, "SKIP", model.file,
                             "schema and example payload generated successfully, but the "
                             "'jsonschema' package is not installed so they were not cross-validated "
                             "(pip install jsonschema)")]

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(payload, schema)
        except jsonschema.ValidationError as e:
            return [Finding("MS2-20", title, "FAIL", model.file,
                             f"generated example payload does not validate against the generated "
                             f"JSON schema: {e.message}")]

    return [Finding("MS2-20", title, "INFO", model.file,
                     "generated JSON schema validates against the generated example payload")]


# --- MS2-21 -----------------------------------------------------------
# "file RELEASE_NOTES.md exists and contains entries for proposed model
# changes"
def check_21_release_notes(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "RELEASE_NOTES.md exists and documents this version"
    if not model.namespace:
        return [Finding("MS2-21", title, "FAIL", model.file, "could not determine this model's namespace")]

    release_notes = Path(model.namespace) / "RELEASE_NOTES.md"
    if not release_notes.exists():
        return [Finding("MS2-21", title, "FAIL", model.file, f"{release_notes} does not exist")]

    findings = []
    text = release_notes.read_text(encoding="utf-8")
    if model.version and not re.search(re.escape(f"[{model.version}]"), text):
        findings.append(Finding("MS2-21", title, "WARN", model.file,
                                 f"{release_notes} has no entry mentioning '[{model.version}]'"))
    if str(release_notes) not in ctx.changed_files:
        findings.append(Finding("MS2-21", title, "WARN", model.file,
                                 f"{release_notes} was not modified in this PR - verify it already "
                                 f"documents this change"))
    if not findings:
        findings.append(Finding("MS2-21", title, "INFO", model.file,
                                 f"{release_notes} was updated and mentions version {model.version}"))
    return findings


# --- MS2-22 (informational) -----------------------------------------------
# "all contributors to this model are mentioned in copyright header of
# model file"
COPYRIGHT_LINE_RE = re.compile(r"#\s*Copyright\(?c\)?\s+\d{4}\s+(.+?)\s*$", re.MULTILINE)


def check_22_copyright_contributors(model: TTLModel, ctx: Context) -> list[Finding]:
    title = "Contributors mentioned in copyright header (needs human review)"
    header_match = re.match(r"(?:#.*\n)+", model.text)
    header = header_match.group(0) if header_match else ""
    copyright_holders = COPYRIGHT_LINE_RE.findall(header)

    authors = ctx.commit_authors(model.file)

    return [Finding(
        "MS2-22", title, "INFO", model.file,
        f"copyright header lists: {copyright_holders or '(none found)'}; git commit authors for "
        f"this file in this PR: {authors or '(none found)'}. GitHub author names don't map 1:1 to "
        f"the company names used in headers, so please confirm manually that every contributing "
        f"organization is represented.",
    )]


REGISTRY = [
    check_01_samm_validate,
    check_02_camel_case,
    check_03_no_double_underscore,
    check_04_capitalized_elements,
    check_05_lowercase_properties,
    check_06_preferred_name_and_description,
    check_07_property_characteristic_name_conflict,
    check_08_semver_urn,
    check_10_redundant_prefixes,
    check_11_preferred_name_not_equal_description,
    check_12_preferred_name_readable,
    check_13_aspect_singular_plural,
    check_14_units_from_catalog,
    check_15_constraints_used,
    check_16_external_standards_see,
    check_17_example_values,
    check_18_imported_models_release_state,
    check_19_own_metadata_release_state,
    check_20_schema_validates_payload,
    check_21_release_notes,
    check_22_copyright_contributors,
]
