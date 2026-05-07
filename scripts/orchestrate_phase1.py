from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcrobotcombatevents.workflow import scrape_event_to_file


SPREADSHEET_URL_RE = re.compile(r"https://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_-]+")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.stdout


def _extract_spreadsheet_url(output: str) -> str:
    match = SPREADSHEET_URL_RE.search(output)
    if not match:
        raise RuntimeError("Could not find created spreadsheet URL in rce2sheet output.")
    return match.group(0)


def _sheet_titles_from_event_json(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    titles: list[str] = []
    for comp in data.get("competitions", []):
        title = comp.get("competition_name") or comp.get("competition_id") or ""
        if title:
            titles.append(str(title))
    return titles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 1: export RCE event JSON, create Google Sheet, and write a manifest file.",
    )
    parser.add_argument("event_id", type=int, help="RobotCombatEvents event ID")
    parser.add_argument("--title", help="Spreadsheet title for rce2sheet")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="build",
        help="Output directory for event JSON and manifest (default: build)",
    )
    parser.add_argument(
        "--manifest",
        help="Optional explicit manifest path (default: <output-dir>/event_<id>_assets.json)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (PROJECT_ROOT / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    event_json = (output_dir / f"event_{args.event_id}.json").resolve()
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = (PROJECT_ROOT / manifest_path).resolve()
    else:
        manifest_path = (output_dir / f"event_{args.event_id}_assets.json").resolve()

    print(f"[1/3] Exporting event {args.event_id} to {event_json}...")
    scrape_event_to_file(args.event_id, str(event_json), indent=2)

    if not event_json.exists():
        raise RuntimeError(
            f"Export command reported success, but event JSON was not found at: {event_json}"
        )

    print(f"[2/3] Creating spreadsheet from {event_json}...")
    rce2sheet_cmd = [sys.executable, "-m", "rce2sheet.cli", str(event_json)]
    if args.title:
        rce2sheet_cmd.extend(["--title", args.title])
    rce2sheet_output = _run_cmd(rce2sheet_cmd)

    spreadsheet_url = _extract_spreadsheet_url(rce2sheet_output)
    spreadsheet_id = spreadsheet_url.rstrip("/").split("/")[-1]
    sheet_titles = _sheet_titles_from_event_json(event_json)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "event_id": args.event_id,
        "event_json": str(event_json),
        "spreadsheet_url": spreadsheet_url,
        "spreadsheet_id": spreadsheet_id,
        "approved_participants_json": str((output_dir / f"approved_participants_{args.event_id}.json").resolve()),
        "competitions": [{"sheet_title": title} for title in sheet_titles],
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[3/3] Wrote manifest: {manifest_path}")
    print("Phase 1 complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
