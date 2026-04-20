"""Tests for cronwatch.silence_store."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.silence_store import load_silencer, save_silencer
from cronwatch.silencer import Silencer, SilenceWindow


def _utc(**kwargs) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(**kwargs)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "silence_state.json"


@pytest.fixture()
def populated_silencer() -> Silencer:
    s = Silencer()
    s.add(SilenceWindow(
        job_name="backup",
        start=_utc(hours=-1),
        end=_utc(hours=2),
        reason="planned maintenance",
    ))
    return s


def test_save_creates_file(state_path, populated_silencer):
    save_silencer(populated_silencer, state_path)
    assert state_path.exists()


def test_round_trip_preserves_windows(state_path, populated_silencer):
    save_silencer(populated_silencer, state_path)
    loaded = load_silencer(state_path)
    windows = loaded.all_windows()
    assert len(windows) == 1
    assert windows[0].job_name == "backup"
    assert windows[0].reason == "planned maintenance"


def test_load_missing_file_returns_empty(tmp_path):
    result = load_silencer(tmp_path / "nonexistent.json")
    assert isinstance(result, Silencer)
    assert result.all_windows() == []


def test_load_malformed_file_returns_empty(state_path):
    state_path.write_text("not valid json", encoding="utf-8")
    result = load_silencer(state_path)
    assert isinstance(result, Silencer)
    assert result.all_windows() == []


def test_save_creates_parent_dirs(tmp_path):
    deep_path = tmp_path / "a" / "b" / "silence.json"
    silencer = Silencer()
    save_silencer(silencer, deep_path)
    assert deep_path.exists()
