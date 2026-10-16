#!/usr/bin/env python3
"""AIM1000 bounded batch pipeline: qualify, deduplicate, prepare resumes, build review dashboard.

This program never submits applications, answers employer declarations, or sends messages.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from application_queue import (
    DB_DEFAULT,
    PROFILE_DEFAULT,
    RESUME_DIR_DEFAULT,
    build_resume,
    connect,
    import_csv,
    now,
    transition,
    validate_profile,
)

ROOT = Path(__file__).resolve().parent
LEADS_DEFAULT = ROOT / "Sniper_Hourly_Leads.csv"
QUALIFIED_DEFAULT = ROOT / "Qualified_Jobs.csv"
DASHBOARD_DEFAULT = ROOT / "Mission_Control.html"
MAX_BATCH_SIZE = 1000


def html_text(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def local_file_href(file_path: Path, dashboard_path: Path) -> str:
    try:
        relative = os.path.relpath(file_path.resolve(), dashboard_path.parent.resolve())
        return quote(Path(relative).as_posix(), safe="/-_.~")
    except (OSError, ValueError):
        return file_path.resolve().as_uri()


def write_dashboard(conn, dashboard_path: Path) -> int:
    rows = conn.execute(
        """SELECT id,title,company,location,canonical_url,score,score_reason,status,resume_path
           FROM jobs WHERE resume_path <> ''
           ORDER BY score DESC, company COLLATE NOCASE, title COLLATE NOCASE"""
    ).fetchall()
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "<!doctype html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>AIM1000 Mission Control</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1200px;margin:0 auto;padding:20px;color:#172033;background:#f6f8fb}",
        "h1{margin-bottom:4px}.muted{color:#596579}.wrap{overflow-x:auto;background:white;border:1px solid #dce3ec;border-radius:10px}",
        "table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;border-bottom:1px solid #e8edf3;vertical-align:top}",
        "th{background:#eaf0f7}.score{font-variant-numeric:tabular-nums;font-weight:700}",
        "a{color:#155eef}.status{white-space:nowrap;font-size:12px}code{overflow-wrap:anywhere}",
        "</style></head><body>",
        "<h1>AIM1000 · Mission Control</h1>",
        "<p class='muted'>Role-specific resume preparation queue. This dashboard does not submit applications.</p>",
        f"<p><strong>{len(rows)}</strong> saved resume artifact(s) · Generated {html_text(now())}</p>",
        "<div class='wrap'><table><thead><tr><th>Score</th><th>Role / Company</th><th>Status</th><th>Reason</th><th>Actions</th></tr></thead><tbody>",
    ]
    for row in rows:
        job_url = str(row["canonical_url"] or "")
        resume_path = Path(str(row["resume_path"] or ""))
        if resume_path.is_file():
            resume_href = local_file_href(resume_path, dashboard_path)
            resume_link = f"<a href='{html_text(resume_href)}' target='_blank' rel='noopener noreferrer'>Review resume PDF</a>"
        else:
            resume_link = "<span class='muted'>Resume file missing — regenerate</span>"
        if job_url.startswith(("https://", "http://")):
            job_link = f"<a href='{html_text(job_url)}' target='_blank' rel='noopener noreferrer'>Open job</a>"
        else:
            job_link = "<span class='muted'>Invalid job URL</span>"
        lines.append(
            "<tr>"
            f"<td class='score'>{int(row['score'] or 0)}</td>"
            f"<td><strong>{html_text(row['title'])}</strong><br>{html_text(row['company'])}"
            f"<br><span class='muted'>{html_text(row['location'])}</span></td>"
            f"<td class='status'>{html_text(row['status'])}</td>"
            f"<td>{html_text(row['score_reason'])}</td>"
            f"<td>{job_link}<br>{resume_link}</td>"
            "</tr>"
        )
    if not rows:
        lines.append("<tr><td colspan='5'>No resume artifacts yet. Run the batch pipeline after completing candidate profile review.</td></tr>")
    lines.extend(["</tbody></table></div>",
                  "<p class='muted'>Check each PDF and employer form yourself. AIM1000 does not click Apply or Submit.</p>",
                  "</body></html>"])
    dashboard_path.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def run(args) -> int:
    if not 1 <= args.max_jobs <= MAX_BATCH_SIZE:
        print(f"ERROR: --max-jobs must be between 1 and {MAX_BATCH_SIZE}.", file=sys.stderr)
        return 2
    if not 0 <= args.min_score <= 100:
        print("ERROR: --min-score must be between 0 and 100.", file=sys.stderr)
        return 2
    if not args.input.is_file():
        print(f"ERROR: lead CSV not found: {args.input}", file=sys.stderr)
        return 2
    if args.input.resolve() == args.qualified_csv.resolve():
        print("ERROR: input and qualified-output paths must differ.", file=sys.stderr)
        return 2
    if not args.profile.is_file():
        print(f"ERROR: candidate profile not found: {args.profile}", file=sys.stderr)
        print("Copy candidate_profile.example.json to candidate_profile.json and enter verified facts first.", file=sys.stderr)
        return 2

    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read candidate profile: {exc}", file=sys.stderr)
        return 2
    profile_errors = validate_profile(profile)
    if profile_errors:
        print("PROFILE NOT READY — no jobs were processed:", file=sys.stderr)
        for error in profile_errors:
            print(f"- {error}", file=sys.stderr)
        print("Correct candidate_profile.json and run: python application_queue.py profile-check", file=sys.stderr)
        return 2

    args.qualified_csv.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(ROOT / "job_filter_agent.py"),
        "--input", str(args.input.resolve()),
        "--output", str(args.qualified_csv.resolve()),
        "--min-score", str(args.min_score),
        "--profile", str(args.profile.resolve()),
    ]
    try:
        completed = subprocess.run(command, cwd=ROOT, timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired:
        print(f"ERROR: job qualification exceeded {args.timeout} seconds.", file=sys.stderr)
        return 2
    if completed.returncode:
        print(f"ERROR: job qualification failed with exit code {completed.returncode}.", file=sys.stderr)
        return completed.returncode

    args.db.parent.mkdir(parents=True, exist_ok=True)
    inserted = updated = prepared = 0
    failures: list[str] = []
    try:
        with connect(args.db) as conn:
            inserted, updated = import_csv(conn, args.qualified_csv)
            candidates = conn.execute(
                """SELECT id,status,score,title,company FROM jobs
                   WHERE status IN ('DISCOVERED','QUALIFIED') AND score >= ?
                   ORDER BY score DESC, created_at ASC, id ASC LIMIT ?""",
                (args.min_score, args.max_jobs),
            ).fetchall()
            for candidate in candidates:
                job_id = int(candidate["id"])
                try:
                    if candidate["status"] == "DISCOVERED":
                        transition(conn, job_id, "QUALIFIED",
                                   f"Batch pipeline qualification score {candidate['score']}")
                    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
                    pdf_path = build_resume(job, profile, args.resume_dir)
                    conn.execute(
                        "UPDATE jobs SET resume_path=?,updated_at=? WHERE id=?",
                        (str(pdf_path.resolve()), now(), job_id),
                    )
                    transition(conn, job_id, "PREPARED", f"Resume prepared for review: {pdf_path}")
                    print(f"PREPARED [{prepared + 1}/{len(candidates)}] {job['company']} — {job['title']}")
                    prepared += 1
                except Exception as exc:
                    failures.append(f"job #{job_id} {candidate['company']} — {candidate['title']}: {type(exc).__name__}: {exc}")
                    print(f"FAILED job #{job_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            dashboard_count = write_dashboard(conn, args.dashboard)
            counts = {
                row["status"]: int(row["n"])
                for row in conn.execute("SELECT status,COUNT(*) AS n FROM jobs GROUP BY status")
            }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: batch processing stopped: {exc}", file=sys.stderr)
        return 2

    print("\n=== AIM1000 BATCH REPORT ===")
    print(f"Lead CSV: {args.input}")
    print(f"Unique qualified CSV: {args.qualified_csv}")
    print(f"Database: {args.db}")
    print(f"New jobs: {inserted} | Existing URLs refreshed: {updated}")
    print(f"Resumes prepared this run: {prepared} | Preparation failures: {len(failures)}")
    print(f"Resumes visible in Mission Control: {dashboard_count}")
    print(f"Queue counts: {json.dumps(counts, sort_keys=True)}")
    print(f"Dashboard: {args.dashboard}")
    print("No applications were submitted. Review every resume and submit manually only after approval.")
    if failures:
        print("\nFailures to inspect:")
        for failure in failures[:25]:
            print(f"- {failure}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=LEADS_DEFAULT, help="CSV of job leads")
    parser.add_argument("--qualified-csv", type=Path, default=QUALIFIED_DEFAULT, help="Scored/deduplicated output")
    parser.add_argument("--profile", type=Path, default=PROFILE_DEFAULT, help="Candidate-reviewed JSON profile")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT, help="Local SQLite queue")
    parser.add_argument("--resume-dir", type=Path, default=RESUME_DIR_DEFAULT, help="Output directory for PDFs")
    parser.add_argument("--dashboard", type=Path, default=DASHBOARD_DEFAULT, help="Local HTML review dashboard")
    parser.add_argument("--max-jobs", type=int, default=MAX_BATCH_SIZE, help="Prepare at most 1,000 jobs per run")
    parser.add_argument("--min-score", type=int, default=25, help="Minimum qualification score, 0-100")
    parser.add_argument("--timeout", type=int, default=180, help="Qualification stage timeout in seconds")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
