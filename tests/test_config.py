"""Tests for cronwatch configuration loader."""

import os
import pytest
import tempfile
import yaml

from cronwatch.config import load_config, CronwatchConfig, JobConfig, AlertConfig


SAMPLE_CONFIG = {
    "check_interval": 120,
    "state_file": "/tmp/test_state.json",
    "jobs": [
        {
            "name": "test-job",
            "schedule": "* * * * *",
            "timeout": 60,
            "grace_period": 10,
            "tags": ["test"],
        }
    ],
    "alerts": {
        "webhook_url": "https://hooks.example.com/test",
        "email": "test@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 465,
    },
}


@pytest.fixture
def config_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(SAMPLE_CONFIG, f)
        path = f.name
    yield path
    os.unlink(path)


def test_load_config_returns_cronwatch_config(config_file):
    config = load_config(config_file)
    assert isinstance(config, CronwatchConfig)


def test_load_config_jobs(config_file):
    config = load_config(config_file)
    assert len(config.jobs) == 1
    job = config.jobs[0]
    assert isinstance(job, JobConfig)
    assert job.name == "test-job"
    assert job.schedule == "* * * * *"
    assert job.timeout == 60
    assert job.grace_period == 10
    assert job.tags == ["test"]


def test_load_config_alerts(config_file):
    config = load_config(config_file)
    alert = config.alerts
    assert isinstance(alert, AlertConfig)
    assert alert.webhook_url == "https://hooks.example.com/test"
    assert alert.email == "test@example.com"
    assert alert.smtp_port == 465


def test_load_config_top_level(config_file):
    config = load_config(config_file)
    assert config.check_interval == 120
    assert config.state_file == "/tmp/test_state.json"


def test_load_config_defaults():
    minimal = {"jobs": [{"name": "j", "schedule": "* * * * *"}], "alerts": {}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(minimal, f)
        path = f.name
    try:
        config = load_config(path)
        assert config.check_interval == 60
        assert config.jobs[0].timeout == 3600
        assert config.jobs[0].grace_period == 300
    finally:
        os.unlink(path)


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/cronwatch.yml")
