"""CLI entry point for cronwatch."""
import argparse
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.monitor import Monitor
from cronwatch.tracker import JobTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron jobs and alert on failures or missed runs.",
    )
    parser.add_argument(
        "-c", "--config",
        default="cronwatch/cronwatch.yml",
        help="Path to cronwatch YAML config file (default: cronwatch/cronwatch.yml)",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Run a one-shot check of all monitored jobs.")

    run_parser = subparsers.add_parser("run", help="Record a job run.")
    run_parser.add_argument("job", help="Job name as defined in config.")
    run_parser.add_argument(
        "--exit-code", type=int, default=0, dest="exit_code",
        help="Exit code of the job (default: 0).",
    )
    run_parser.add_argument(
        "--duration", type=float, default=None, dest="duration",
        help="Duration of the job in seconds.",
    )
    return parser


def cmd_check(config_path: str) -> int:
    config = load_config(config_path)
    tracker = JobTracker()
    monitor = Monitor(config, tracker)
    alerts = monitor.check_all()
    if alerts:
        print(f"[cronwatch] {len(alerts)} alert(s) dispatched.")
        for alert in alerts:
            print(f"  - {alert}")
        return 1
    print("[cronwatch] All jobs healthy.")
    return 0


def cmd_run(config_path: str, job_name: str, exit_code: int, duration: float | None) -> int:
    config = load_config(config_path)
    job_cfg = next((j for j in config.jobs if j.name == job_name), None)
    if job_cfg is None:
        print(f"[cronwatch] Unknown job: {job_name}", file=sys.stderr)
        return 2
    tracker = JobTracker()
    run = tracker.record_start(job_name)
    tracker.record_finish(run, exit_code=exit_code, duration_seconds=duration)
    status = "succeeded" if run.succeeded else "failed"
    print(f"[cronwatch] Recorded run for '{job_name}': {status}")
    return 0 if run.succeeded else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check(args.config)
    if args.command == "run":
        return cmd_run(args.config, args.job, args.exit_code, args.duration)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
