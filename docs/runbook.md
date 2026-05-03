# Runbook — drupal-crawl-for-ai

## First run

```bash
# Install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run extraction
drupal-crawl issues --project 3060 --format both
```

This will:
1. Create a run in `runs/<run_id>/manifest.json`
2. Write JSONL to `data/normalized/<run_id>/records.jsonl`
3. Write Markdown to `data/normalized/<run_id>/markdown/`
4. Cache API responses in `data/raw/cache/`

---

## Resumed run

If a run was interrupted, resume it:

```bash
drupal-crawl issues --project 3060 --resume-run <run_id>
```

The run ID is printed at the start of each run. You can also find it in `runs/` (each subdirectory is a run ID).

Verify resume worked:
```bash
cat runs/<run_id>/manifest.json | python -m json.tool | grep -E '"status"|"succeeded"|"fetched"'
```

---

## Troubleshooting 429 / 5xx

### 429 Too Many Requests

Increase the delay between requests:
```bash
drupal-crawl issues --project 3060 --delay-seconds 5.0
```

### 5xx Server Errors

These are automatically retried with exponential backoff (up to 5 attempts). If failures persist:
1. Check Drupal.org status at https://www.drupal.org
2. Wait before retrying
3. Use `--max-retries 3` to fail faster for debugging

### Inspect failures

```bash
cat runs/<run_id>/manifest.json | python -m json.tool | jq '.failures'
```

---

## Cache cleanup policy

Cached responses live in `data/raw/cache/` with a 7-day TTL by default.

**When to clear:**
- After Drupal.org data has meaningfully changed
- When resuming from a very old run
- To force fresh API fetches

**How to clear:**
```bash
rm -rf data/raw/cache/
# Or for a specific endpoint:
rm data/raw/cache/*.json
```

**How to bypass cache for a run:**
```bash
# Use a new run_id (don't use --resume-run)
drupal-crawl issues --project 3060
```

---

## Output formats

| Format | Output | Use case |
|--------|--------|----------|
| `jsonl` | `data/normalized/<run_id>/records.jsonl` | Downstream processing, AI training pipelines |
| `markdown` | `data/normalized/<run_id>/markdown/` | Human review, context for LLMs |
| `both` (default) | Both of the above | Full fidelity |

### JSONL format

Each line is a valid JSON object:
```json
{"cid": 123, "nid": 456, "record_type": "issue_comment", ...}
```

### Markdown format

Files are named by entity type and ID:
```
data/normalized/<run_id>/markdown/project_issue/3060.md
```

Each file has a frontmatter header:
```markdown
---
record_type: project_issue
id: 3060
fetched_at: 2025-01-01T00:00:00+00:00
source_url: https://www.drupal.org/api-d7/node/3060.json
---

# Issue Title

Body content...
```

---

## Common workflows

### Extract multiple projects
```bash
drupal-crawl issues --project 3060 --project 12345 --project 67890
```

### Limit issue count (for testing)
```bash
drupal-crawl issues --project 3060 --max-issues 10
```

### Extract issue with comments
```bash
drupal-crawl issue --nid 3332546 --include-comments --format both
```

### Full bundle for a project
```bash
drupal-crawl issue-bundle --project 3060 --include-related-mrs --format both
```