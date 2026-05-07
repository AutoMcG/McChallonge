from __future__ import annotations

import argparse
import json
import subprocess
import sys
import webbrowser
from pathlib import Path


def _run_cmd(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _run_bulk_add(approved_json: Path, tournament_id: str, sheet_title: str, verbose: bool) -> None:
    # Prefer the installed console script for clearer execution semantics.
    cmd = [
        "mcchallonge-bulk-add",
        str(approved_json),
        tournament_id,
        "--competition",
        sheet_title,
    ]
    if verbose:
        cmd.append("--verbose")

    try:
        _run_cmd(cmd)
    except FileNotFoundError:
        # Fallback for environments where the console script isn't on PATH.
        fallback_cmd = [
            sys.executable,
            "-m",
            "mcchallonge.cli.bulk_add_participants",
            str(approved_json),
            tournament_id,
            "--competition",
            sheet_title,
        ]
        if verbose:
            fallback_cmd.append("--verbose")
        _run_cmd(fallback_cmd)


def _open_dashboard_browser() -> None:
    try:
        webbrowser.open_new_tab("http://localhost:8000")
    except Exception:
        # Browser launch is best-effort.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 2: read approved participants from spreadsheet and bulk-add them to "
            "Challonge tournaments per sheet title."
        )
    )
    parser.add_argument(
        "manifest",
        help="Path to manifest JSON created by scripts/orchestrate_phase1.py",
    )
    parser.add_argument(
        "--approved-json",
        help="Override output path for approved participants JSON",
    )
    parser.add_argument(
        "--mapping-file",
        help=(
            "Optional JSON file for non-interactive tournament mappings by sheet title. "
            "Supports either an object {\"Sheet Title\": \"tournament_id\"} "
            "or a list of objects with sheet_title/tournament_id keys."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Pass --verbose to mcchallonge-bulk-add calls",
    )
    parser.add_argument(
        "--skip-serve",
        action="store_true",
        help="Do not launch mcchallonge.app serve after imports",
    )
    return parser


def _load_mapping_file(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    mappings: dict[str, str] = {}

    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip():
                mappings[key.strip()] = value.strip()
        return mappings

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            sheet_title = item.get("sheet_title")
            tournament_id = item.get("tournament_id")
            if isinstance(sheet_title, str) and isinstance(tournament_id, str):
                if sheet_title.strip() and tournament_id.strip():
                    mappings[sheet_title.strip()] = tournament_id.strip()
        return mappings

    raise RuntimeError("Mapping file must be a JSON object or a JSON list of mapping objects.")


def _prompt_tournament_id(sheet_title: str) -> str | None:
    while True:
        value = input(
            f"Tournament ID for '{sheet_title}' (leave blank to skip): "
        ).strip()
        if value:
            return value
        confirm = input("Skip this sheet? [y/N]: ").strip().lower()
        if confirm in {"y", "yes"}:
            return None


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    spreadsheet_url = manifest.get("spreadsheet_url")
    if not spreadsheet_url:
        raise RuntimeError("Manifest is missing 'spreadsheet_url'.")

    approved_json = Path(args.approved_json or manifest.get("approved_participants_json", "approved_participants.json"))
    approved_json.parent.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Reading approvals from spreadsheet: {spreadsheet_url}")
    _run_cmd([
        sys.executable,
        "-m",
        "rce2sheet.reader",
        spreadsheet_url,
        "-o",
        str(approved_json),
    ])

    approved_data = json.loads(approved_json.read_text(encoding="utf-8"))
    competitions = approved_data.get("competitions", [])
    if not competitions:
        print("No competitions found in approved participants JSON. Nothing to import.")
        return 0

    mappings: list[tuple[str, str]] = []
    if args.mapping_file:
        print(f"[2/3] Loading non-interactive mappings from {args.mapping_file}...")
        mapping_by_title = _load_mapping_file(Path(args.mapping_file))
        for comp in competitions:
            sheet_title = comp.get("sheet_title", "")
            if not sheet_title:
                continue
            tournament_id = mapping_by_title.get(sheet_title)
            if tournament_id:
                mappings.append((sheet_title, tournament_id))
            else:
                print(f"  {sheet_title}: no mapping found, skipping.")
    else:
        print("[2/3] Prompting tournament mapping by sheet title...")
        for comp in competitions:
            sheet_title = comp.get("sheet_title", "")
            if not sheet_title:
                continue
            tournament_id = _prompt_tournament_id(sheet_title)
            if tournament_id:
                mappings.append((sheet_title, tournament_id))

    if not mappings:
        print("No tournament mappings provided. Nothing to import.")
        return 0

    print("[3/3] Importing approved participants into Challonge...")
    for sheet_title, tournament_id in mappings:
        print(f"Importing '{sheet_title}' into tournament '{tournament_id}'...")
        _run_bulk_add(approved_json, tournament_id, sheet_title, args.verbose)

    if not args.skip_serve:
        print("[4/4] Launching dashboard server on port 8000...")
        _open_dashboard_browser()
        _run_cmd([
            sys.executable,
            "-m",
            "mcchallonge.app",
            "serve",
            "--port",
            "8000",
            "--threads",
            "2",
        ])

    print("Phase 2 complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
