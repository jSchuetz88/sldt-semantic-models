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
# Posts a Finding as an inline PR review comment via the GitHub REST API,
# for criteria that opt in via ``POST_COMMENT = True`` (see criteria/__init__.py).
#
# Stdlib-only (urllib), matching the rest of this package's "no external
# dependencies beyond the optional jsonschema check" approach.
#
# Silently does nothing (prints a one-line note instead) whenever posting
# isn't possible or doesn't make sense, rather than failing the check run:
#   - not running on a `pull_request` event (e.g. local run, push, schedule)
#   - no GITHUB_TOKEN available, or the token lacks `pull-requests: write`
#   - the finding has no line (see report.Finding.line)
#   - the finding's line isn't part of this PR's diff (GitHub's review
#     comment API only accepts lines that appear in the diff; hitting this
#     is expected whenever the offending line predates this PR)
#
# One real limitation of this first version: comments are only ever
# created, never updated. A HIDDEN_MARKER embedded in the comment body
# identifies "a comment for this criterion+file+line already exists" so
# re-running the check (e.g. on a new push to the same PR) doesn't spam
# duplicates - but if the *message* changes between runs, the stale comment
# is left as-is rather than being edited.

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from functools import lru_cache

from .report import Finding

API_ROOT = "https://api.github.com"
HIDDEN_MARKER = "<!-- ms2-check:{criterion_id}:{path}:{line} -->"


@dataclass(frozen=True)
class PRContext:
    owner: str
    repo: str
    pull_number: int
    commit_sha: str


def _pr_context() -> PRContext | None:
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    if not event_path or not repo_slug:
        return None
    try:
        event = json.loads(open(event_path, encoding="utf-8").read())
        owner, repo = repo_slug.split("/", 1)
        return PRContext(
            owner=owner,
            repo=repo,
            pull_number=event["pull_request"]["number"],
            commit_sha=event["pull_request"]["head"]["sha"],
        )
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def _api_request(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, object]:
    url = f"{API_ROOT}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


@lru_cache(maxsize=None)
def _existing_comment_bodies(pr: PRContext, token: str) -> tuple[str, ...]:
    # Fetched once per run (not per finding) and cached - a matrix leg only
    # checks one model but may post several comments for it.
    status, payload = _api_request(
        "GET", f"/repos/{pr.owner}/{pr.repo}/pulls/{pr.pull_number}/comments?per_page=100", token)
    if status != 200 or not isinstance(payload, list):
        return ()
    return tuple(c.get("body", "") for c in payload)


def post_review_comment(finding: Finding, criterion_id: str) -> None:
    if finding.line is None:
        return

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(f"{criterion_id}: GITHUB_TOKEN not set - skipping inline PR comment")
        return

    pr = _pr_context()
    if pr is None:
        # Expected for local runs and non-PR CI triggers - not worth a log line.
        return

    marker = HIDDEN_MARKER.format(criterion_id=criterion_id, path=finding.file, line=finding.line)
    if any(marker in body for body in _existing_comment_bodies(pr, token)):
        return  # already posted for this criterion/file/line in an earlier run of this PR

    icon = "❌" if finding.level == "FAIL" else "⚠️"
    body = f"{marker}\n{icon} **{criterion_id} - {finding.title}**\n\n{finding.message}"

    status, payload = _api_request(
        "POST", f"/repos/{pr.owner}/{pr.repo}/pulls/{pr.pull_number}/comments", token,
        body={
            "body": body,
            "commit_id": pr.commit_sha,
            "path": finding.file,
            "line": finding.line,
            "side": "RIGHT",
        },
    )
    if status not in (200, 201):
        # Most common cause: `line` isn't part of this PR's diff (GitHub
        # rejects those with 422) - not a bug in the check itself, so this
        # stays a log line, not a crash.
        message = payload.get("message", payload) if isinstance(payload, dict) else payload
        print(f"{criterion_id}: could not post inline PR comment on {finding.file}:{finding.line}: {message}")
