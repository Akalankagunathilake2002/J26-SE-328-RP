"""Step 8: the daily sync, run by the job-market-sync Docker container (see README).

    python -m app.collectors.schedule            # keep running: sync once a day
    python -m app.collectors.schedule --status   # the last sync and when the next one is due

Every hour it checks whether a sync is due. One is due once the day's sync time has passed
(SKILLBRIDGE_SYNC_TIME, default 06:00 Sri Lanka time) and no sync has finished since. So a sync
missed while the computer or Docker was off runs as soon as they are back, and the schedule
syncs at most once a day. A sync that fails (e.g. no internet) is tried again an hour later, at
most MAX_ATTEMPTS times a day, so a site that asked us to stop is not asked again and again.

Each sync is the same as scripts/sync.sh: `python -m app.collectors.run --site all --sector all
--sync`, in its own process, with its output added to data/logs/sync-<date>.log.

It runs in Docker rather than as a macOS launchd job because macOS doesn't let background jobs
read ~/Documents, where the project lives; Docker Desktop already has access to it.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time as clock
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, time, timedelta, timezone
from pathlib import Path

from app.collectors.config import SERVICE_ROOT, load_settings
from app.collectors.storage import Storage

SRI_LANKA = timezone(timedelta(hours=5, minutes=30), "+0530")  # no daylight saving time
DEFAULT_TIME = "06:00"
DEFAULT_LIMIT = 25  # new ads per sector and site, as in scripts/sync.sh
CHECK_EVERY = 3600  # seconds
MAX_ATTEMPTS = 3  # syncs tried per day
STATE_FILE = "scheduler.json"  # in data/logs/: the attempts since the last sync time
SYNC_COMMAND = [sys.executable, "-m", "app.collectors.run", "--site", "all", "--sector", "all", "--sync", "--limit"]

log = logging.getLogger("schedule")

Runner = Callable[[Path, int, datetime], int]


def parse_time(value: str) -> time:
    try:
        hour, minute = value.split(":")
        return time(int(hour), int(minute))
    except ValueError:
        raise ValueError(f"the sync time must be HH:MM (Sri Lanka time), not {value!r}") from None


def latest_slot(now: datetime, at: time) -> datetime:
    """The most recent sync time: today's if it has passed, otherwise yesterday's."""
    local = now.astimezone(SRI_LANKA)
    slot = datetime.combine(local.date(), at, tzinfo=SRI_LANKA)
    return slot if slot <= local else slot - timedelta(days=1)


def last_sync(storage: Storage) -> datetime | None:
    """When the last sync of any site finished (data/processed/sync_log.csv)."""
    times = [datetime.fromisoformat(row["synced_at"]) for row in storage.read_sync_log() if row.get("synced_at")]
    return max(times, default=None)


def is_due(last: datetime | None, slot: datetime, attempts: int) -> bool:
    return (last is None or last < slot) and attempts < MAX_ATTEMPTS


def attempts_since(storage: Storage, slot: datetime) -> int:
    path = storage.root / "logs" / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return 0
    return int(state.get("attempts", 0)) if state.get("slot") == slot.isoformat() else 0


def record_attempt(storage: Storage, slot: datetime, attempts: int) -> None:
    path = storage.root / "logs" / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"slot": slot.isoformat(), "attempts": attempts}), encoding="utf-8")


def run_sync(data_dir: Path, limit: int, started: datetime) -> int:
    """One sync in its own process, with its output added to data/logs/sync-<date>.log."""
    local = started.astimezone(SRI_LANKA)
    path = data_dir / "logs" / f"sync-{local:%Y-%m-%d}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as out:
        out.write(f"=== scheduled sync started {local:%Y-%m-%d %H:%M:%S} Sri Lanka time ===\n")
        out.flush()
        process = subprocess.Popen([*SYNC_COMMAND, str(limit)], stdout=out, stderr=subprocess.STDOUT, cwd=SERVICE_ROOT)
        try:
            return process.wait()
        except BaseException:  # the container is being stopped
            process.send_signal(signal.SIGINT)  # lets the run remove its lock file
            process.wait(timeout=10)
            raise


def check(storage: Storage, at: time, limit: int, now: datetime | None = None, runner: Runner = run_sync) -> int | None:
    """Run the sync if it is due. Returns its exit code, or None when none was due."""
    now = now or datetime.now(UTC)
    slot = latest_slot(now, at)
    attempts = attempts_since(storage, slot)
    if not is_due(last_sync(storage), slot, attempts):
        return None
    record_attempt(storage, slot, attempts + 1)
    log.info("sync started (attempt %d of %d today)", attempts + 1, MAX_ATTEMPTS)
    code = runner(storage.root, limit, now)
    if code == 0:
        log.info("sync finished")
    elif attempts + 1 < MAX_ATTEMPTS:
        log.warning("sync failed (exit code %d, see data/logs/); trying again in an hour", code)
    else:
        log.warning("sync failed (exit code %d, see data/logs/); no more tries until the next sync time", code)
    return code


def status(storage: Storage, at: time, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    slot = latest_slot(now, at)
    last, attempts = last_sync(storage), attempts_since(storage, slot)
    lines = [f"Daily sync at {at:%H:%M} Sri Lanka time."]
    if last is None:
        lines.append("Last sync: never.")
    else:
        days = (now - last).days
        ago = "today" if days == 0 else "1 day ago" if days == 1 else f"{days} days ago"
        lines.append(f"Last sync: {last.astimezone(SRI_LANKA):%Y-%m-%d %H:%M} Sri Lanka time ({ago}).")
    if is_due(last, slot, attempts):
        lines.append("Next sync: due now (it starts within the hour while the container runs).")
    else:
        if last is None or last < slot:
            lines.append(f"The {slot:%Y-%m-%d} sync failed {attempts} times; see data/logs/.")
        lines.append(f"Next sync: {slot + timedelta(days=1):%Y-%m-%d %H:%M} Sri Lanka time.")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync the job sites once a day.")
    parser.add_argument("--at", default=os.environ.get("SKILLBRIDGE_SYNC_TIME") or DEFAULT_TIME,
                        help="sync time, HH:MM in Sri Lanka time (default: SKILLBRIDGE_SYNC_TIME or 06:00)")
    parser.add_argument("--limit", type=int, default=int(os.environ.get("SYNC_LIMIT") or DEFAULT_LIMIT),
                        help="new ads per sector and site (default: SYNC_LIMIT or 25)")
    parser.add_argument("--status", action="store_true", help="show the last and the next sync, then exit")
    args = parser.parse_args(argv)
    try:
        at = parse_time(args.at)
    except ValueError as exc:
        parser.error(str(exc))
    storage = Storage(load_settings().data_dir)

    if args.status:
        print(status(storage, at))
        return 0

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # docker stop
    log.info("daily sync at %s Sri Lanka time; checking every hour", f"{at:%H:%M}")
    while True:
        check(storage, at, args.limit)
        clock.sleep(CHECK_EVERY)


if __name__ == "__main__":
    sys.exit(main())
