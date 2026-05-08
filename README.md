# Drupal Crawl for AI

Polite, rerunnable Python extractors for Drupal.org content used in AI training/context pipelines.

## Mission

Build a stable extraction pipeline for:

- Drupal change notices (`type=changenotice`)
- Drupal issue queues (`type=project_issue`)
- Issue comments (`comment.json?node=<nid>`)
- Related metadata needed for downstream knowledge artifacts

The pipeline is API-first, deterministic, and fully checkpointed for resume.

---

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Requires Python 3.10+.

---

## Venv Survival Guide

After a workspace compaction or fresh clone, the `.venv` may be gone or broken. To get running again:

```bash
# 1. Recreate venv
python3 -m venv .venv

# 2. Activate (must be done before any pip install or drupal-crawl call)
source .venv/bin/activate

# 3. Install locked dev environment (runtime + test/lint/typecheck tools)
pip install -r requirements-dev.txt
```

### Dependency management policy (best practice)

- **Source of truth:** `pyproject.toml`
- **Reproducible installs:** `requirements.txt` and `requirements-dev.txt` (generated, pinned)
- **No manual ad-hoc installs in docs**

Refresh lockfiles only when dependencies intentionally change:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pip-compile pyproject.toml -o requirements.txt
pip-compile pyproject.toml --extra dev -o requirements-dev.txt
```

Then commit: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` together.

**On every new shell session**, you must run `source .venv/bin/activate` before using `drupal-crawl`, `pytest`, `ruff`, or `mypy`. The `drupal-crawl` command only exists inside the activated venv.

**Aliases** — add to your shell profile (or `.agents.env` in the repo root) for convenience:

```bash
alias va='source .venv/bin/activate'       # activate venv
alias crawl='.venv/bin/drupal-crawl'         # run without activating
alias test='va && pytest tests/ -q'          # run tests
alias lint='va && ruff check src tests'      # lint
```

---

## CLI Usage

All commands share: `--delay-seconds`, `--max-retries`, `--max-pages`, `--output-root`, `--runs-root`, `--format` (jsonl|markdown|both), `--resume-run`.

### Change notices

```bash
source .venv/bin/activate
drupal-crawl changes --project 3060 --max-pages 5 --format jsonl
```

### Issue queue

```bash
drupal-crawl issues --project 3060 --max-pages 5 --format both
drupal-crawl issues --project 3060 --project 12345 --max-issues 100 --max-pages 20
```

### Single issue

```bash
drupal-crawl issue --nid 3382735 --include-comments --format jsonl
```

### Full issue bundle (queue + details + comments)

```bash
drupal-crawl issue-bundle --project 3060 --max-pages 5 --max-issues 50 --format both
```

### Resume an interrupted run

```bash
drupal-crawl issues --project 3060 --resume-run <run_id>
```

### Output

All output goes under `--output-root` (default: `data`):

```
data/normalized/<run_id>/records.jsonl   # canonical JSONL records
data/normalized/<run_id>/markdown/        # rendered Markdown files
runs/<run_id>/manifest.json              # run manifest + counters
data/raw/cache/                          # cached API responses (7-day TTL)
```

To clear cache: `rm -rf data/raw/cache/`

---

## Politeness Defaults

- **Single-threaded** — one request at a time
- **2.0s delay** between calls (configurable via `--delay-seconds`)
- **Retry with backoff** on `429` and `5xx` (max 5 retries)
- **User-Agent**: `drupal-crawl-for-ai/<version> (+https://github.com/...)`
- **Accept**: `application/json`

---

## Resume and Cache Reuse

Each run writes a manifest to `runs/<run_id>/manifest.json` tracking:
- pagination cursor position
- counters (fetched, succeeded, failed, cache_hits)
- failures

When you re-run with `--resume-run <run_id>`, extraction continues from the last checkpoint. Cache in `data/raw/cache/` stores responses with 7-day TTL to avoid re-fetching unchanged data.

To clear cache: `rm -rf data/raw/cache/`

---

## Repository Layout

```text
src/drupal_crawl_ai/
├── cli.py                  # Click CLI entrypoint
├── config.py               # Config dataclasses
├── http/
│   ├── client.py          # Polite HTTP client (retry, pacing)
│   └── cache.py           # Read-through response cache
├── api/
│   ├── nodes.py           # Node API helper
│   ├── comments.py        # Comment API helper
│   └── pagination.py      # Pagination iterator
├── discovery/
│   └── project_lookup.py  # Project alias resolution
├── extractors/
│   ├── changes.py         # Change notices
│   ├── issues.py          # Issue queue
│   ├── issue_details.py   # Single issue
│   ├── issue_comments.py # Comments per issue
│   └── issue_bundle.py    # Full bundle orchestrator
├── normalize/
│   ├── records.py         # Canonical record normalizers
│   └── markdown.py        # HTML→Markdown renderer
├── storage/
│   ├── manifest.py        # Run manifest + checkpoint
│   ├── writer.py          # Unified output writer
│   ├── writer_jsonl.py    # JSONL append writer
│   └── writer_markdown.py # Per-entity markdown writer
└── schemas/               # JSON schemas for records
data/
├── raw/cache/            # Cached API responses
├── raw/<run_id>/         # Raw payloads per run
└── normalized/<run_id>/   # Canonical + markdown output
runs/<run_id>/manifest.json
```

---

## Current Status

**V2 implementation is complete.** All milestones A–J and I are implemented:
- Package scaffold, tooling, quality gates
- HTTP primitives with polite pacing and caching
- API helpers with pagination
- Run manifests with checkpoint/resume
- Canonical schemas, normalizers, markdown renderer
- JSONL and markdown storage writers
- Extractors for changes, issues, issue details, comments, and bundles
- Project alias resolution
- Full Click CLI with validation

Milestones K (README, runbook) and L (verification gate) are the final steps.

---

## License

MIT License
