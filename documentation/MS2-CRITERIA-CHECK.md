# Automated MS2 Criteria Check

This describes the automated check that runs on every pull request to verify the MS2 checklist items from [`PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) against the changed Aspect Models. It complements, but does not replace, the manual MS2 review described in [`GOVERNANCE.md`](GOVERNANCE.md) - some checklist items are objectively checkable (Camel-Case, semantic versioning, `metadata.json` state, ...), others require human judgement and stay manual (see the "Automation" column in the criteria table below).

## Where everything lives

```text
.github/
├── PULL_REQUEST_TEMPLATE.md          the 22 MS2 checklist items this check implements
├── workflows/
│   └── governance.yml                the CI pipeline (3 jobs, see below)
└── scripts/
    ├── ms2_check.py                  master script / CLI entry point
    └── model-validation/             the actual package
        ├── config.json               per-repo settings & criterion overrides
        ├── config.py                 loads config.json
        ├── context.py                shared state handed to every criterion (repo root,
        │                             changed files, lazily-downloaded SAMM CLI jar)
        ├── samm_cli.py                downloads/runs the SAMM CLI jar
        ├── samm_model_parser.py       lightweight Turtle/SAMM parser (no RDF library)
        ├── report.py                  Finding type + Markdown table rendering
        └── criteria/                  one file per MS2 checklist item
            ├── __init__.py            auto-discovers every cNN_*.py below into REGISTRY
            ├── c01_samm_validate.py
            ├── c02_camel_case.py
            ├── ...
            └── c22_copyright_contributors.py
```

## CI pipeline (`governance.yml`)

The pipeline is split into three jobs specifically so that **every changed model gets its own check mark** in the PR UI, while still having one reliable, fixed-name check to mark as *required* in branch protection:

1. **`detect-changed-models`** - the only job that checks out full repository history. Runs `git diff origin/main...HEAD` (three dots: diffs against the merge-base, i.e. what *this branch* changed since it forked from `main`, independent of whatever landed on `main` afterwards) to find every changed file. Outputs two lists as job outputs:
   - `files`: just the changed `.ttl` files - becomes the matrix below
   - `all_files`: every changed file - handed to each matrix leg so they don't each need to recompute a diff (see next job)

2. **`ms2-criteria-check`** - a matrix job, one run per entry in `files`. Each run is named `Check MS2 Criteria (<path>)`, so each changed model shows up as its own, separately visible check. Each leg:
   - does a **shallow** checkout (`fetch-depth: 1`) - no repo history needed, since it already got the full changed-files list from `detect-changed-models` via `--changed-files`
   - restores/saves the SAMM CLI jar from an `actions/cache` entry keyed on a hash of `config.json` (where the pinned SAMM CLI version lives), so only the first leg per version actually downloads the ~110 MB jar
   - runs `ms2_check.py --file <path> --changed-files <json>` for that one model

   This job is deliberately **not** the one you mark as a required status check: its name (and how many runs of it exist) varies per PR depending on which models changed, and GitHub branch protection can only pin down fixed, known check names.

3. **`ms2-criteria-gate`** - fixed name (`Summary Check`), `if: always()`, waits on the matrix job and fails if any leg failed. This is the one to mark as required in branch protection: it always runs (even with zero changed models, where the matrix is skipped entirely and this job just passes trivially), so it's always selectable and never leaves a required check stuck pending.

## The master script (`ms2_check.py`)

Single CLI entry point, run three different ways by `governance.yml` (see the file's own header comment for the exact flags):

| Mode | Used by | What it does |
| --- | --- | --- |
| `--list-changed-files` | `detect-changed-models` | prints the changed `.ttl` files as JSON, nothing else |
| `--list-all-changed-files` | `detect-changed-models` | prints *every* changed file as JSON (feeds `--changed-files`) |
| `--file <path> --changed-files <json>` | each `ms2-criteria-check` matrix leg | checks exactly one model, no git diff needed |
| (no flags) | local/manual runs | auto-detects and checks every changed `.ttl` file via its own `git diff` |

For each file, it: parses the model, loads `config.json`, then hands the parsed model plus a shared `Context` to every enabled criterion in `criteria.REGISTRY`, downgrading `FAIL` to `WARN` for criteria configured as non-blocking, collects all findings, prints them, writes the Markdown report to the job summary, and exits non-zero if anything is still `FAIL`.

## Criteria (`model-validation/criteria/`)

Each `cNN_<slug>.py` is a self-contained sub-routine exposing `ID`, `TITLE`, and `check(model, ctx) -> list[Finding]`. `criteria/__init__.py` builds `REGISTRY` by importing every `cNN_*.py` file in numeric order and collecting the ones that define `check` - a file without one (like `c09_abbreviations.py`) still shows up in the folder for the overview, but is silently skipped.

**To add or change a criterion:** drop in (or edit) a `cNN_<slug>.py` file with `ID`, `TITLE`, and a `check` function. Nothing else needs to change - no registry to update by hand.

Each `Finding` has a level:

| Level | Icon in report | Meaning |
| --- | --- | --- |
| `FAIL` | ❌ | objectively violates the MS2 rule, breaks the CI check |
| `WARN` | ⚠️ | heuristic or non-certain violation, doesn't break CI, needs human review |
| `INFO` | ✅ | nothing wrong found (used for a genuine pass, and synthesized by the master script for a criterion that stays silent when it finds nothing to flag) |
| `SKIP` | ➖ | couldn't be evaluated (e.g. no Java/network for the SAMM CLI) or disabled via config |

### The 22 checklist items

| ID | Automation | Notes |
| --- | --- | --- |
| MS2-01 | ✅ automated | runs `samm-cli aspect <file> validate` for real |
| MS2-02 | ✅ automated | Camel-Case identifiers |
| MS2-03 | ✅ automated | no `__` in identifiers/payload names |
| MS2-04 | ✅ automated | non-property identifiers start uppercase |
| MS2-05 | ✅ automated | property identifiers start lowercase |
| MS2-06 | ✅ automated | `preferredName`/`description` present, English |
| MS2-07 | ✅ automated | property and its Characteristic don't share a name |
| MS2-08 | ✅ automated | URN version is valid semver and matches its folder |
| MS2-09 | ⛔ not automated | "abbreviations only when necessary" is a judgement call - no `check` function, stays a manual review item on purpose |
| MS2-10 | ⚠️ heuristic | redundant property-name prefixes - flags, doesn't fail |
| MS2-11 | ✅ automated | `preferredName` != `description` |
| MS2-12 | ✅ automated | `preferredName` is human-readable, not Camel-Case |
| MS2-13 | ✅ automated (partial) | plural aspect name required for a single Collection-valued property; the reverse (must be singular) isn't enforced, too unreliable |
| MS2-14 | ⚠️ heuristic | units should come from the SAMM catalog - flags, doesn't fail |
| MS2-15 | ℹ️ informational | constraints usage - only reports what's there, can't judge if more are needed |
| MS2-16 | ℹ️ informational | `samm:see` usage - same reasoning as MS2-15 |
| MS2-17 | ✅ automated | simple-typed properties have an example value |
| MS2-18 | ✅ automated | imported/external models are in `release` state |
| MS2-19 | ✅ automated | own `metadata.json` exists with status `release` |
| MS2-20 | ✅ automated | generated JSON schema validates the generated example payload |
| MS2-21 | ✅ automated | `RELEASE_NOTES.md` exists and mentions this version |
| MS2-22 | ✅ automated (partial) | only checks a copyright header exists; matching it against actual contributors isn't reliably automatable (GitHub usernames vs. company names) |

## Config (`model-validation/config.json`)

Two sections, both optional - a missing or empty file behaves exactly like default settings for everything:

```json
{
  "settings": {
    "samm_cli_version": "2.11.1"
  },
  "criteria": {
    "MS2-15": { "blocking": false },
    "MS2-19": { "enabled": false }
  }
}
```

- **`settings.samm_cli_version`** - the SAMM CLI version to download and run (MS2-01/MS2-20). Single source of truth; deliberately *not* parsed out of `README.md` prose, so it can't silently drift and doesn't invalidate the SAMM CLI cache on unrelated README edits.
- **`criteria.<ID>.enabled`** (default `true`) - set to `false` to skip a criterion entirely (shows as `SKIP`/➖, no further detail).
- **`criteria.<ID>.blocking`** (default `true`) - set to `false` to keep a criterion running and reporting, but downgrade any `FAIL` it produces to `WARN` so it no longer breaks the `ms2-criteria-gate` check. Still a MUST per the PR template, just not (yet) enforced automatically.

A criterion ID in the config that doesn't match any known criterion prints a `WARNING:` line in the job log (typo protection) but doesn't fail the run.

## Report format

Written to the GitHub Actions job summary (and printed to the console). One section per checked model, headed by the model's file path, followed by a table with one row per criterion: status icon, criterion ID, criterion name, and message. A criterion that produces multiple findings for the same model shows the worst icon and all messages (`<br>`-joined) in one row. Messages are wrapped in an inline code span for monospace rendering, since real line breaks aren't possible inside a Markdown table cell - collapsible `<details>` sections were tried for long multi-line output (e.g. a full samm-cli error dump) but GitHub's job-summary sanitizer strips that tag entirely, so plain inline code is what's left.

## Running locally

```bash
# check every .ttl file changed on this branch vs. origin/main
python .github/scripts/ms2_check.py

# check one specific file
python .github/scripts/ms2_check.py --file io.catenax.batch/4.0.0/Batch.ttl
```

Run from the repository root. MS2-01/MS2-20 need Java on `PATH` to run the SAMM CLI; without it they report `SKIP` rather than failing the whole run. MS2-20's JSON-schema-vs-payload cross-validation additionally needs the `jsonschema` Python package (`pip install jsonschema`) - without it, schema and payload still get generated, just not cross-validated.
