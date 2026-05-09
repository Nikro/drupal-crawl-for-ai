# AGENTS.md

Purpose: persistent guardrails for AI agents working in this repository.

## Project mission

This repository builds **polite, rerunnable Python data extractors** for Drupal.org content used in AI training/context pipelines.

Primary targets:
- Change notices / change records
- Issue queues
- Issue comments
- Related metadata needed to build structured knowledge artifacts

## Core operating rules (non-negotiable)

1. **API-first, HTML-second**
   - Prefer Drupal.org `api-d7` endpoints for bulk reads.
   - Use HTML scraping only when necessary (for discovery gaps like missing IDs/index pages).
   - If HTML is used, keep it minimal and only for bootstrap/discovery.

2. **Be polite to Drupal.org**
   - Single-threaded request flow by default.
   - Conservative pacing between requests (default: >=1s; increase when needed).
   - Clear `User-Agent` identifying this tool/repo.
   - Respect rate limits, backoff on 429/5xx, and never hammer endpoints.

3. **Do not re-run identical extractions unnecessarily**
   - Cache responses locally.
   - Persist run manifests/checkpoints.
   - Reuse prior run outputs when inputs/scope are unchanged.
   - Support resume after interruption.

4. **Deterministic, rerunnable pipeline behavior**
   - Same inputs should produce same normalized outputs.
   - Keep source provenance (URL, params, timestamp, entity IDs).
   - Store normalized records in structured formats (JSON/JSONL) before downstream transforms.

5. **Safety and legality**
   - Read-only collection only.
   - No auth bypass, no stealth scraping behavior, no evasion tactics.
   - Follow Drupal.org automation and API guidance.

## Drupal API guidance for this repo

- Base query endpoints:
  - `https://www.drupal.org/api-d7/node.json`
  - `https://www.drupal.org/api-d7/comment.json`
- Send `Accept: application/json` (or use `.json` suffix).
- Typical node types:
  - `type=project_issue`
  - `type=changenotice`
- Comments for an issue use **`node=<nid>`** (not `nid=<nid>`).
- Expect pagination (`page`, `limit`) and iterate until no `next` (or empty list).

## Data model and artifact expectations (v2 direction)

The codebase should evolve toward:
- `src/drupal_crawl_ai/schemas/` for canonical JSON schemas
- `data/raw/` for cached source payloads
- `data/normalized/` for cleaned canonical records
- `runs/` for manifests, checkpoints, and run metadata

Each run should record:
- scope (project IDs, branches, filters)
- request parameters and paging position
- created/updated timestamps
- record counts and failure counts

## Implementation expectations for agents

- Keep diffs minimal and scoped.
- Add/adjust tests for parsing, pagination, retry/backoff, and cache reuse logic.
- Prefer composable modules over monolithic scripts.
- Keep CLI entrypoints simple and explicit.
- Never introduce concurrency by default.

## Out of scope unless explicitly requested

- Write actions against Drupal.org
- Aggressive parallel crawling
- Browser automation/stealth scraping
- Large refactors unrelated to extraction pipeline goals

## Practical default headers

- `Accept: application/json`
- `User-Agent: drupal-crawl-for-ai/<version> (+repo/contact URL)`

## Success criteria for future runs

- Pulls required data via API-first flow
- Reuses cached/checkpointed state
- Produces stable structured artifacts for AI ingestion
- Stays polite and non-disruptive to Drupal.org infrastructure
