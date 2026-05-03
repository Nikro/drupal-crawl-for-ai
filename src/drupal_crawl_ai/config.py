"""Run and tool configuration models."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BASE_URL = "https://www.drupal.org/api-d7"
DEFAULT_DELAY_SECONDS = 2.0
DEFAULT_MAX_RETRIES = 5
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_CACHE_TTL_HOURS = 168  # 7 days
DEFAULT_MAX_PAGES = 20
DEFAULT_OUTPUT_FORMAT = "both"
DEFAULT_VERSION = "0.1.0"


@dataclass
class HttpConfig:
    """HTTP client configuration."""

    base_url: str = DEFAULT_BASE_URL
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    user_agent: str = f"drupal-crawl-for-ai/{DEFAULT_VERSION} (+https://github.com/drupal-crawl-for-ai)"
    accept_header: str = "application/json"


@dataclass
class CacheConfig:
    """Response cache configuration."""

    enabled: bool = True
    ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
    cache_root: Path = field(
        default_factory=lambda: Path("data/raw/cache")
    )

    def cache_dir(self) -> Path:
        path = self.cache_root
        path.mkdir(parents=True, exist_ok=True)
        return path


@dataclass
class OutputConfig:
    """Output path configuration."""

    output_root: Path = field(default_factory=lambda: Path("data"))
    runs_root: Path = field(default_factory=lambda: Path("runs"))
    format: str = DEFAULT_OUTPUT_FORMAT  # jsonl | markdown | both

    def raw_dir(self, run_id: str) -> Path:
        d = self.output_root / "raw" / run_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def normalized_dir(self, run_id: str) -> Path:
        d = self.output_root / "normalized" / run_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def runs_dir(self) -> Path:
        d = self.runs_root
        d.mkdir(parents=True, exist_ok=True)
        return d


@dataclass
class RunConfig:
    """Run execution configuration."""

    run_id: str | None = None
    resume_run_id: str | None = None
    max_pages: int = DEFAULT_MAX_PAGES
    max_issues: int | None = None
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    allow_html_discovery: bool = False


@dataclass
class Config:
    """Top-level configuration aggregating all sub-configs."""

    http: HttpConfig = field(default_factory=HttpConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    run: RunConfig = field(default_factory=RunConfig)

    @classmethod
    def from_env(cls) -> Config:
        """Build config from environment variables (optional overrides)."""
        return cls(
            http=HttpConfig(
                base_url=os.getenv("DRUPAL_API_BASE_URL", DEFAULT_BASE_URL),
                delay_seconds=float(
                    os.getenv("DRUPAL_DELAY_SECONDS", str(DEFAULT_DELAY_SECONDS))
                ),
                max_retries=int(
                    os.getenv("DRUPAL_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
                ),
            ),
            cache=CacheConfig(
                enabled=os.getenv("DRUPAL_CACHE_ENABLED", "1") != "0",
                ttl_hours=int(
                    os.getenv("DRUPAL_CACHE_TTL_HOURS", str(DEFAULT_CACHE_TTL_HOURS))
                ),
            ),
        )
