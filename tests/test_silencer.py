"""Tests for cronwatch.silencer."""

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.silencer import Silencer, SilenceWindow


def _utc(**kwargs) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(**kwargs)


@pytest.fixture()
def silencer() -> Silencer:
    return Silencer()


@pytest.fixture()
def active_window() -> SilenceWindow:
    return SilenceWindow(
        job_name="backup",
        start=_utc(hours=-1),
        end=_utc(hours=1),
        reason="maintenance",
    )


@pytest.fixture()
def expired_window() -> SilenceWindow:
    return SilenceWindow(
        job_name="backup",
        start=_utc(hours=-3),
        end=_utc(hours=-1),
    )


def test_is_silenced_when_active(silencer, active_window):
    silencer.add(active_window)
    assert silencer.is_silenced("backup") is True


def test_not_silenced_when_expired(silencer, expired_window):
    silencer.add(expired_window)
    assert silencer.is_silenced("backup") is False


def test_not_silenced_unknown_job(silencer, active_window):
    silencer.add(active_window)
    assert silencer.is_silenced("other_job") is False


def test_active_windows_returns_only_active(silencer, active_window, expired_window):
    silencer.add(active_window)
    silencer.add(expired_window)
    active = silencer.active_windows()
    assert len(active) == 1
    assert active[0].job_name == "backup"


def test_remove_deletes_windows(silencer, active_window):
    silencer.add(active_window)
    removed = silencer.remove("backup")
    assert removed == 1
    assert silencer.is_silenced("backup") is False


def test_remove_returns_zero_for_unknown(silencer):
    assert silencer.remove("nonexistent") == 0


def test_round_trip_serialisation(silencer, active_window):
    silencer.add(active_window)
    restored = Silencer.from_dict(silencer.to_dict())
    assert len(restored.all_windows()) == 1
    w = restored.all_windows()[0]
    assert w.job_name == "backup"
    assert w.reason == "maintenance"


def test_silence_window_is_active_at_specific_time():
    base = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
    window = SilenceWindow(
        job_name="nightly",
        start=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
        end=datetime(2024, 6, 1, 14, 0, tzinfo=timezone.utc),
    )
    assert window.is_active(at=base) is True
    assert window.is_active(at=datetime(2024, 6, 1, 15, 0, tzinfo=timezone.utc)) is False
