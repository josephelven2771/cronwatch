"""Tests for the cronwatch CLI."""
import pytest
from unittest.mock import MagicMock, patch

from cronwatch.cli import build_parser, main


@pytest.fixture()
def config_path(tmp_path):
    cfg = tmp_path / "cronwatch.yml"
    cfg.write_text(
        "jobs:\n"
        "  - name: backup\n"
        "    schedule: '0 2 * * *'\n"
        "    max_silence_seconds: 90000\n"
        "alerts:\n"
        "  webhook_url: null\n"
        "  email: null\n"
    )
    return str(cfg)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["check"])
    assert args.command == "check"
    assert args.config == "cronwatch/cronwatch.yml"


def test_build_parser_run_subcommand():
    parser = build_parser()
    args = parser.parse_args(["run", "backup", "--exit-code", "1"])
    assert args.command == "run"
    assert args.job == "backup"
    assert args.exit_code == 1


def test_main_no_command_returns_zero():
    result = main([])
    assert result == 0


def test_main_check_healthy(config_path):
    with patch("cronwatch.cli.Monitor") as MockMonitor:
        MockMonitor.return_value.check_all.return_value = []
        result = main(["-c", config_path, "check"])
    assert result == 0


def test_main_check_with_alerts(config_path):
    with patch("cronwatch.cli.Monitor") as MockMonitor:
        MockMonitor.return_value.check_all.return_value = ["missed: backup"]
        result = main(["-c", config_path, "check"])
    assert result == 1


def test_main_run_unknown_job(config_path):
    result = main(["-c", config_path, "run", "nonexistent"])
    assert result == 2


def test_main_run_known_job_success(config_path):
    with patch("cronwatch.cli.JobTracker") as MockTracker:
        mock_run = MagicMock(succeeded=True)
        MockTracker.return_value.record_start.return_value = mock_run
        result = main(["-c", config_path, "run", "backup"])
    assert result == 0


def test_main_run_known_job_failure(config_path):
    with patch("cronwatch.cli.JobTracker") as MockTracker:
        mock_run = MagicMock(succeeded=False)
        MockTracker.return_value.record_start.return_value = mock_run
        result = main(["-c", config_path, "run", "backup", "--exit-code", "1"])
    assert result == 1
