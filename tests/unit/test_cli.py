"""Unit tests for CLI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from drupal_crawl_ai.cli import cli


def test_help_command_shows_all_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "changes" in result.output
    assert "issues" in result.output
    assert "issue" in result.output
    assert "issue-bundle" in result.output


def test_changes_command_runs(tmp_path):
    runner = CliRunner()
    with patch("drupal_crawl_ai.extractors.changes.NodesApi") as mock_nodes_cls:
        mock_api = MagicMock()
        mock_api.query_all.return_value = iter([{"list": []}])
        mock_nodes_cls.return_value = mock_api

        result = runner.invoke(cli, [
            "changes",
            "--project", "3060",
            "--output-root", str(tmp_path / "data"),
            "--runs-root", str(tmp_path / "runs"),
            "--delay-seconds", "0.01",
        ])
    assert result.exit_code == 0


def test_issues_command_requires_project(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "issues",
        "--output-root", str(tmp_path / "data"),
        "--runs-root", str(tmp_path / "runs"),
        "--delay-seconds", "0.01",
    ])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_issue_command_requires_nid(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "issue",
        "--output-root", str(tmp_path / "data"),
        "--runs-root", str(tmp_path / "runs"),
        "--delay-seconds", "0.01",
    ])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_issue_bundle_command_requires_project(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "issue-bundle",
        "--output-root", str(tmp_path / "data"),
        "--runs-root", str(tmp_path / "runs"),
        "--delay-seconds", "0.01",
    ])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_max_pages_rejects_zero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "changes",
        "--project", "3060",
        "--max-pages", "0",
        "--output-root", str(tmp_path / "data"),
        "--runs-root", str(tmp_path / "runs"),
        "--delay-seconds", "0.01",
    ])
    # max-pages 0 should be rejected (must be >= 1)
    assert result.exit_code != 0
