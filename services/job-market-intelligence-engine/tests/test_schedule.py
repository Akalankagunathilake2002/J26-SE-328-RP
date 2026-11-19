"""Step 8: the daily sync schedule and the lock that keeps two runs apart. No network, no Docker."""

import sys
from datetime import UTC, datetime, time

import pytest

from app.collectors import run as run_module
from app.collectors import schedule
from app.collectors.config import Settings
from app.collectors.run import LOCK_FILE, RunInProgress, run_lock
from app.collectors.run import main as run_main
from app.collectors.schedule import MAX_ATTEMPTS, check, latest_slot, parse_time, status
from app.collectors.storage import Storage

SIX = time(6, 0)


def utc(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def synced(storage, at):
    storage.append_sync_log({"synced_at": at, "site": "topjobs"})


class Runner:
    """Stands in for a real sync: records the call, and logs a sync when it 'succeeds'."""

    def __init__(self, storage, code=0):
        self.storage, self.code, self.calls = storage, code, 0

    def __call__(self, data_dir, limit, now):
        self.calls += 1
        if self.code == 0:
            synced(self.storage, now.isoformat())
        return self.code


def test_the_latest_sync_time_is_today_once_it_has_passed_in_sri_lanka():
    # 06:00 in Sri Lanka is 00:30 UTC
    assert latest_slot(utc("2026-11-19T00:29:00"), SIX).isoformat() == "2026-11-18T06:00:00+05:30"
    assert latest_slot(utc("2026-11-19T00:30:00"), SIX).isoformat() == "2026-11-19T06:00:00+05:30"
    # 01:30 on the 20th in Sri Lanka: the 20th's sync time hasn't come yet
    assert latest_slot(utc("2026-11-19T20:00:00"), SIX).isoformat() == "2026-11-19T06:00:00+05:30"
    assert parse_time("21:15") == time(21, 15)
    with pytest.raises(ValueError):
        parse_time("6am")


def test_a_sync_runs_once_a_day_after_the_sync_time(tmp_path):
    storage = Storage(tmp_path)
    runner = Runner(storage)

    assert check(storage, SIX, 25, utc("2026-11-19T02:00:00"), runner) == 0  # never synced: due
    assert check(storage, SIX, 25, utc("2026-11-19T03:00:00"), runner) is None  # done for today
    assert check(storage, SIX, 25, utc("2026-11-19T23:00:00"), runner) is None  # 04:30 next day, before 06:00
    assert check(storage, SIX, 25, utc("2026-11-20T01:00:00"), runner) == 0  # the next day's sync
    assert runner.calls == 2


def test_a_missed_sync_runs_when_the_computer_is_back(tmp_path):
    storage = Storage(tmp_path)
    synced(storage, "2026-10-22T04:52:56+00:00")  # off for weeks
    runner = Runner(storage)

    assert check(storage, SIX, 25, utc("2026-11-19T10:00:00"), runner) == 0
    assert runner.calls == 1


def test_a_sync_by_hand_after_the_sync_time_counts_for_the_day(tmp_path):
    storage = Storage(tmp_path)
    synced(storage, "2026-11-19T02:00:00+00:00")  # scripts/sync.sh at 07:30 in Sri Lanka
    runner = Runner(storage)

    assert check(storage, SIX, 25, utc("2026-11-19T05:00:00"), runner) is None
    assert runner.calls == 0


def test_a_failing_sync_is_tried_a_few_times_a_day_only(tmp_path):
    storage = Storage(tmp_path)
    runner = Runner(storage, code=1)

    codes = [check(storage, SIX, 25, utc(f"2026-11-19T{hour:02d}:00:00"), runner) for hour in range(1, 7)]

    assert codes == [1] * MAX_ATTEMPTS + [None] * (6 - MAX_ATTEMPTS)
    assert "failed 3 times" in status(storage, SIX, utc("2026-11-19T07:00:00"))
    assert check(storage, SIX, 25, utc("2026-11-20T01:00:00"), runner) == 1  # tried again the next day


def test_status(tmp_path):
    storage = Storage(tmp_path)
    assert "Last sync: never." in status(storage, SIX, utc("2026-11-19T02:00:00"))

    synced(storage, "2026-10-22T04:52:56+00:00")
    text = status(storage, SIX, utc("2026-11-19T02:00:00"))
    assert "Last sync: 2026-10-22 10:22 Sri Lanka time (27 days ago)." in text
    assert "due now" in text

    synced(storage, "2026-11-19T01:00:00+00:00")
    assert "Next sync: 2026-11-20 06:00 Sri Lanka time." in status(storage, SIX, utc("2026-11-19T02:00:00"))


def test_run_sync_adds_the_output_to_the_day_log(tmp_path, monkeypatch):
    monkeypatch.setattr(schedule, "SYNC_COMMAND", [sys.executable, "-c", "import sys; print('synced, limit', sys.argv[1])"])

    assert schedule.run_sync(tmp_path, 25, utc("2026-11-19T20:00:00")) == 0

    log = (tmp_path / "logs" / "sync-2026-11-20.log").read_text()  # the date in Sri Lanka
    assert "scheduled sync started 2026-11-20 01:30:00 Sri Lanka time" in log
    assert "synced, limit 25" in log


def test_only_one_run_at_a_time(tmp_path):
    with run_lock(tmp_path):
        assert (tmp_path / LOCK_FILE).exists()
        with pytest.raises(RunInProgress):
            with run_lock(tmp_path):
                pass
    assert not (tmp_path / LOCK_FILE).exists()  # released


def test_a_lock_left_by_a_killed_run_is_replaced(tmp_path, monkeypatch):
    (tmp_path / LOCK_FILE).write_text("old run")
    monkeypatch.setattr(run_module, "STALE_LOCK_SECONDS", 0)

    with run_lock(tmp_path):
        assert "old run" not in (tmp_path / LOCK_FILE).read_text()


def test_a_run_while_another_is_running_changes_nothing(tmp_path, capsys):
    (tmp_path / LOCK_FILE).write_text("job-market-sync, pid 7, started 2026-11-19T00:30:00+00:00")

    assert run_main(["--site", "topjobs", "--reparse", "--no-ocr"], settings=Settings(tmp_path, None)) == 1
    assert "another run is using" in capsys.readouterr().err
    assert not (tmp_path / "processed").exists()
