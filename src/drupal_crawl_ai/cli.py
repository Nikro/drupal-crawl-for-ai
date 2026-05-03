"""CLI entrypoint for drupal-crawl-for-ai."""

from __future__ import annotations

from pathlib import Path

import click

from drupal_crawl_ai.config import CacheConfig, Config, HttpConfig, OutputConfig
from drupal_crawl_ai.extractors.changes import ChangesExtractor
from drupal_crawl_ai.extractors.issue_bundle import IssueBundleExtractor
from drupal_crawl_ai.extractors.issue_comments import IssueCommentsExtractor
from drupal_crawl_ai.extractors.issue_details import IssueDetailsExtractor
from drupal_crawl_ai.extractors.issues import IssuesExtractor
from drupal_crawl_ai.storage.manifest import RunManifest
from drupal_crawl_ai.storage.writer import Writer


def _validate_date(param_name: str, value: str | None) -> str | None:
    """Validate date format YYYY-MM-DD. Raises click.BadParameter on invalid."""
    if value is None:
        return None
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise click.BadParameter(
            f"{param_name} must be YYYY-MM-DD, got: {value}"
        )
    return value


def _build_config(
    output_root: str,
    runs_root: str,
    delay_seconds: float,
    format: str,
    cache_ttl_hours: int,
) -> Config:
    return Config(
        http=HttpConfig(delay_seconds=delay_seconds),
        cache=CacheConfig(ttl_hours=cache_ttl_hours),
        output=OutputConfig(
            output_root=Path(output_root),
            runs_root=Path(runs_root),
            format=format,
        ),
    )


@click.group()
@click.option("--debug", is_flag=True)
def cli(debug: bool) -> None:
    """drupal-crawl-for-ai — Polite, rerunnable Drupal.org data extractors."""
    pass


@cli.command()
@click.option("--project", "-p", "projects", multiple=True, type=int, help="Project NID(s)")
@click.option("--to-branch")
@click.option("--changed-since")
@click.option("--changed-until")
@click.option("--created-since")
@click.option("--created-until")
@click.option(
    "--format",
    "output_format",
    default="both",
    type=click.Choice(["jsonl", "markdown", "both"]),
)
@click.option("--delay-seconds", default=2.0, type=float)
@click.option("--max-pages", default=20, type=click.IntRange(min=1, max=1000))
@click.option("--max-retries", default=5, type=int)
@click.option("--cache-ttl-hours", default=168, type=int)
@click.option("--output-root", default="data", type=click.Path())
@click.option("--runs-root", default="runs", type=click.Path())
@click.option("--resume-run")
@click.option("--allow-html-discovery", is_flag=True)
def changes(
    projects: tuple[int, ...],
    to_branch: str | None,
    changed_since: str | None,
    changed_until: str | None,
    created_since: str | None,
    created_until: str | None,
    output_format: str,
    delay_seconds: float,
    max_pages: int,
    max_retries: int,
    cache_ttl_hours: int,
    output_root: str,
    runs_root: str,
    resume_run: str | None,
    allow_html_discovery: bool,
) -> None:
    changed_since = _validate_date("--changed-since", changed_since)
    changed_until = _validate_date("--changed-until", changed_until)
    created_since = _validate_date("--created-since", created_since)
    created_until = _validate_date("--created-until", created_until)

    cfg = _build_config(output_root, runs_root, delay_seconds, output_format, cache_ttl_hours)
    cfg.http.max_retries = max_retries
    cfg.run.allow_html_discovery = allow_html_discovery

    if resume_run:
        manifest = RunManifest.load(resume_run, config=cfg)
    else:
        manifest = RunManifest(config=cfg)
        manifest.write_initial("changes", {"projects": list(projects)})
    writer = Writer(Path(output_root), manifest.run_id, format=output_format)

    try:
        extractor = ChangesExtractor(writer=writer, manifest=manifest, config=cfg)
        extractor.extract(
            projects=list(projects),
            to_branch=to_branch,
            changed_since=changed_since,
            changed_until=changed_until,
            created_since=created_since,
            created_until=created_until,
            max_pages=max_pages,
        )
        manifest.mark_completed()
    except Exception as e:
        manifest.mark_failed(str(e))
        raise


@cli.command("issues")
@click.option(
    "--project", "-p", "projects", multiple=True, type=int, required=True, help="Project NID(s)"
)
@click.option("--status", default="any")
@click.option("--priority")
@click.option("--changed-since")
@click.option("--changed-until")
@click.option(
    "--format",
    "output_format",
    default="both",
    type=click.Choice(["jsonl", "markdown", "both"]),
)
@click.option("--delay-seconds", default=2.0, type=float)
@click.option("--max-pages", default=20, type=click.IntRange(min=1, max=1000))
@click.option("--max-issues", type=int)
@click.option("--max-retries", default=5, type=int)
@click.option("--cache-ttl-hours", default=168, type=int)
@click.option("--output-root", default="data", type=click.Path())
@click.option("--runs-root", default="runs", type=click.Path())
@click.option("--resume-run")
@click.option("--allow-html-discovery", is_flag=True)
def issues(
    projects: tuple[int, ...],
    status: str,
    priority: str | None,
    changed_since: str | None,
    changed_until: str | None,
    output_format: str,
    delay_seconds: float,
    max_pages: int,
    max_issues: int | None,
    max_retries: int,
    cache_ttl_hours: int,
    output_root: str,
    runs_root: str,
    resume_run: str | None,
    allow_html_discovery: bool,
) -> None:
    changed_since = _validate_date("--changed-since", changed_since)
    changed_until = _validate_date("--changed-until", changed_until)

    cfg = _build_config(output_root, runs_root, delay_seconds, output_format, cache_ttl_hours)
    cfg.http.max_retries = max_retries
    cfg.run.allow_html_discovery = allow_html_discovery

    if resume_run:
        manifest = RunManifest.load(resume_run, config=cfg)
    else:
        manifest = RunManifest(config=cfg)
        manifest.write_initial("issues", {"projects": list(projects)})
    writer = Writer(Path(output_root), manifest.run_id, format=output_format)

    try:
        extractor = IssuesExtractor(writer=writer, manifest=manifest, config=cfg)
        extractor.extract(
            projects=list(projects),
            status=status,
            priority=priority,
            changed_since=changed_since,
            changed_until=changed_until,
            max_pages=max_pages,
            max_issues=max_issues,
        )
        manifest.mark_completed()
    except Exception as e:
        manifest.mark_failed(str(e))
        raise


@cli.command("issue")
@click.option("--nid", type=int, required=True, help="Issue NID")
@click.option("--include-comments", is_flag=True)
@click.option("--include-related-mrs", is_flag=True)
@click.option(
    "--format",
    "output_format",
    default="both",
    type=click.Choice(["jsonl", "markdown", "both"]),
)
@click.option("--delay-seconds", default=2.0, type=float)
@click.option("--max-retries", default=5, type=int)
@click.option("--cache-ttl-hours", default=168, type=int)
@click.option("--output-root", default="data", type=click.Path())
@click.option("--runs-root", default="runs", type=click.Path())
@click.option("--resume-run")
def issue(
    nid: int,
    include_comments: bool,
    include_related_mrs: bool,
    output_format: str,
    delay_seconds: float,
    max_retries: int,
    cache_ttl_hours: int,
    output_root: str,
    runs_root: str,
    resume_run: str | None,
) -> None:
    cfg = _build_config(output_root, runs_root, delay_seconds, output_format, cache_ttl_hours)
    cfg.http.max_retries = max_retries

    if resume_run:
        manifest = RunManifest.load(resume_run, config=cfg)
    else:
        manifest = RunManifest(config=cfg)
        manifest.write_initial("issue", {"nid": nid})
    writer = Writer(Path(output_root), manifest.run_id, format=output_format)

    try:
        extractor = IssueDetailsExtractor(config=cfg)
        record = extractor.extract(nid=nid, include_related_mrs=include_related_mrs)
        writer.write_record(record)

        if include_comments:
            comments_ext = IssueCommentsExtractor(writer=writer, manifest=manifest, config=cfg)
            comments_ext.extract(issue_nid=nid)

        manifest.mark_completed()
    except Exception as e:
        manifest.mark_failed(str(e))
        raise


@cli.command("issue-bundle")
@click.option(
    "--project", "-p", "projects", multiple=True, type=int, required=True,
)
@click.option("--include-related-mrs", is_flag=True)
@click.option("--include-extra-credit", is_flag=True)
@click.option(
    "--format",
    "output_format",
    default="both",
    type=click.Choice(["jsonl", "markdown", "both"]),
)
@click.option("--delay-seconds", default=2.0, type=float)
@click.option("--max-pages", default=20, type=click.IntRange(min=1, max=1000))
@click.option("--max-issues", type=int)
@click.option("--max-retries", default=5, type=int)
@click.option("--cache-ttl-hours", default=168, type=int)
@click.option("--output-root", default="data", type=click.Path())
@click.option("--runs-root", default="runs", type=click.Path())
@click.option("--resume-run")
@click.option("--allow-html-discovery", is_flag=True)
def issue_bundle(
    projects: tuple[int, ...],
    include_related_mrs: bool,
    include_extra_credit: bool,
    output_format: str,
    delay_seconds: float,
    max_pages: int,
    max_issues: int | None,
    max_retries: int,
    cache_ttl_hours: int,
    output_root: str,
    runs_root: str,
    resume_run: str | None,
    allow_html_discovery: bool,
) -> None:
    cfg = _build_config(output_root, runs_root, delay_seconds, output_format, cache_ttl_hours)
    cfg.http.max_retries = max_retries
    cfg.run.allow_html_discovery = allow_html_discovery

    if resume_run:
        manifest = RunManifest.load(resume_run, config=cfg)
    else:
        manifest = RunManifest(config=cfg)
        manifest.write_initial("issue-bundle", {"projects": list(projects)})
    writer = Writer(Path(output_root), manifest.run_id, format=output_format)

    try:
        extractor = IssueBundleExtractor(writer=writer, manifest=manifest, config=cfg)
        extractor.extract(
            projects=list(projects),
            include_related_mrs=include_related_mrs,
            include_extra_credit=include_extra_credit,
            max_issues=max_issues,
            max_pages=max_pages,
        )
        manifest.mark_completed()
    except Exception as e:
        manifest.mark_failed(str(e))
        raise


def main() -> None:
    cli()
