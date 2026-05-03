"""Unit tests for config module."""

from drupal_crawl_ai import config
from drupal_crawl_ai.config import (
    CacheConfig,
    Config,
    HttpConfig,
    OutputConfig,
    RunConfig,
)


def test_http_config_defaults() -> None:
    cfg = HttpConfig()
    assert cfg.delay_seconds == config.DEFAULT_DELAY_SECONDS
    assert cfg.max_retries == config.DEFAULT_MAX_RETRIES
    assert "drupal-crawl-for-ai" in cfg.user_agent
    assert cfg.accept_header == "application/json"


def test_cache_config_defaults() -> None:
    cfg = CacheConfig()
    assert cfg.enabled is True
    assert cfg.ttl_hours == config.DEFAULT_CACHE_TTL_HOURS


def test_run_config_defaults() -> None:
    cfg = RunConfig()
    assert cfg.resume_run_id is None
    assert cfg.max_pages == config.DEFAULT_MAX_PAGES
    assert cfg.delay_seconds == config.DEFAULT_DELAY_SECONDS
    assert cfg.allow_html_discovery is False


def test_output_config_defaults() -> None:
    cfg = OutputConfig()
    assert cfg.format == config.DEFAULT_OUTPUT_FORMAT


def test_top_level_config() -> None:
    cfg = Config()
    assert isinstance(cfg.http, HttpConfig)
    assert isinstance(cfg.cache, CacheConfig)
    assert isinstance(cfg.output, OutputConfig)
    assert isinstance(cfg.run, RunConfig)
