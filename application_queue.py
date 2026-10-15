#!/usr/bin/env python3
"""AIM1000 local application queue and job-specific resume preparation.

The queue is local-first (SQLite). It never submits an application automatically.
It can prepare a job-specific PDF from candidate-approved facts, open the job page,
and record a human-confirmed outcome.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_DEFAULT = ROOT / "aim1000.db"
PROFILE_DEFAULT = ROOT / "candidate_profile.json"
RESUME_DIR_DEFAULT = ROOT / "resumes"
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  canonical_url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT DEFAULT '',
  description TEXT DEFAULT '',
  score INTEGER NOT NULL DEFAULT 0,
  score_reason TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'DISCOVERED',
  resume_path TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS application_events (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id),
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  note TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_score ON jobs(status, score DESC);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_url(value: str) -> str:
    value = (value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+$", "", parsed.path)
    return f"{parsed.scheme.lower()}://{host}{path}"


def pick(row: dict, *keys: str) -> str:
    norm = {re.sub(r"[^a-z0-9]", "", str(k).lower()): str(v or "").strip()
            for k, v in row.items()}
    for key in keys:
        value = norm.get(re.sub(r"[^a-z0-9]", "", key.lower()), "")
        if value:
            return value
    return ""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def import_csv(conn: sqlite3.Connection, csv_path: Path) -> tuple[int, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Lead CSV not found: {csv_path}")
    inserted = updated = 0
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Lead CSV has no header row")
        for row in reader:
            url = canonical_url(pick(row, "Apply Link", "Job URL", "URL", "Link"))
            title = pick(row, "Job Title", "Title", "Role", "Position")
            company = pick(row, "Company", "Company Name", "Employer")
            if not url or not title or not company:
                continue
            location = pick(row, "Location", "Job Location")
            description = pick(row, "Description", "JD Snippet", "Job Description", "Summary")
            try:
                score = int(float(pick(row, "qualification_score", "Score") or 0))
            except ValueError:
                score = 0
            reason = pick(row, "qualification_reason", "Score Reason")
            stamp = now()
            existed = conn.execute("SELECT 1 FROM jobs WHERE canonical_url=?", (url,)).fetchone() is not None
            conn.execute(
                """INSERT INTO jobs(canonical_url,title,company,location,description,score,
                   score_reason,status,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,'DISCOVERED',?,?)
                   ON CONFLICT(canonical_url) DO UPDATE SET
                     title=excluded.title, company=excluded.company,
                     location=excluded.location, description=excluded.description,
                     score=MAX(jobs.score,excluded.score),
                     score_reason=CASE WHEN excluded.score>=jobs.score THEN excluded.score_reason ELSE jobs.score_reason END,
                     updated_at=excluded.updated_at""",
                (url, title, company, location, description, score, reason, stamp, stamp),
            )
            if existed:
                updated += 1
            else:
                inserted += 1
    conn.commit()
    return inserted, updated


def transition(conn: sqlite3.Connection, job_id: int, target: str, note: str = "") -> None:
    allowed = {
        "DISCOVERED": {"QUALIFIED", "REJECTED"},
        "QUALIFIED": {"PREPARED", "REJECTED"},
        "PREPARED": {"READY_FOR_REVIEW", "QUALIFIED", "REJECTED"},
        "READY_FOR_REVIEW": {"APPLYING", "PREPARED", "REJECTED"},
        "APPLYING": {"SUBMITTED", "NEEDS_HUMAN", "FAILED_RETRYABLE"},
        "FAILED_RETRYABLE": {"READY_FOR_REVIEW", "NEEDS_HUMAN", "REJECTED"},
        "NEEDS_HUMAN": {"READY_FOR_REVIEW", "SUBMITTED", "REJECTED"},
        "SUBMITTED": {"FOLLOW_UP_DUE", "REJECTED"},
        "FOLLOW_UP_DUE": {"SUBMITTED", "REJECTED"},
        "REJECTED": set(),
    }
    row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown job id: {job_id}")
    old = row["status"]
    if target not in allowed.get(old, set()):
        raise ValueError(f"Invalid transition {old} -> {target}")
    stamp = now()
    conn.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", (target, stamp, job_id))
    conn.execute("INSERT INTO application_events(job_id,from_status,to_status,note,created_at) VALUES(?,?,?,?,?)",
                 (job_id, old, target, note, stamp))
    conn.commit()


def build_resume(job: sqlite3.Row, profile: dict, output_dir: Path) -> Path:
    """Create a concise PDF using only facts in the candidate profile."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
    except ImportError as exc:
        raise RuntimeError("PDF generation needs reportlab; install requirements.txt") from exc

    name = str(profile.get("candidate_name", "Candidate")).strip() or "Candidate"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{job['company']}_{job['title']}").strip("_")[:80]
    path = output_dir / f"{safe or 'job'}_{job['id']}_resume.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CandidateName", parent=styles["Title"], fontSize=19, leading=22, alignment=TA_LEFT, spaceAfter=3))
    styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading2"], fontSize=10, leading=12, textColor=colors.HexColor("#174a7e"), spaceBefore=8, spaceAfter=3))
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=8.7, leading=11, spaceAfter=2))
    story = [Paragraph(name, styles["CandidateName"])]
    contacts = [profile.get(k, "") for k in ("email", "phone", "location")]
    links = [profile.get(k, "") for k in ("linkedin_url", "github_url", "portfolio_url")]
    story.append(Paragraph(" | ".join(str(x) for x in contacts + links if x), styles["SmallBody"]))
    story.append(Paragraph(f"{job['title']} — {job['company']}", styles["Heading2"]))
    summary = str(profile.get("summary", "")).strip()
    if summary:
        story.extend([Paragraph("PROFESSIONAL SUMMARY", styles["SectionHead"]), Paragraph(summary, styles["SmallBody"])])
    jd_words = set(re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", (job["title"] + " " + job["description"]).lower()))
    skills = [str(s) for s in profile.get("skills", []) if str(s).strip()]
    # Reorder only existing candidate-provided skills by relevance to this job description.
    skills.sort(key=lambda s: (s.lower() in jd_words, sum(1 for w in re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", s.lower()) if w in jd_words)), reverse=True)
    if skills:
        story.extend([Paragraph("CORE SKILLS", styles["SectionHead"]), Paragraph(" • ".join(skills[:18]), styles["SmallBody"])])
    for heading, key in (("PROFESSIONAL EXPERIENCE", "experience"), ("SELECTED PROJECTS", "projects"), ("EDUCATION", "education"), ("CERTIFICATIONS", "certifications")):
        items = profile.get(key, [])
        if not items:
            continue
        story.append(Paragraph(heading, styles["SectionHead"]))
        for item in items:
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or item.get("degree") or ""
                company = item.get("company", "")
                dates = item.get("dates", "")
                line = " — ".join(str(x) for x in (title, company, dates) if x)
                if line:
                    story.append(Paragraph(line, styles["SmallBody"]))
                url = item.get("url", "")
                if url:
                    story.append(Paragraph(str(url), styles["SmallBody"]))
                bullets = item.get("bullets", [])
                for bullet in bullets:
                    story.append(Paragraph("• " + str(bullet), styles["SmallBody"]))
            else:
                story.append(Paragraph(str(item), styles["SmallBody"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Prepared for this role. All statements are sourced from the candidate profile; verify details before submission.", styles["SmallBody"]))
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=13*mm, bottomMargin=13*mm, title=f"{name} - {job['title']}")
    doc.build(story)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="Import scraped or qualified CSV leads")
    imp.add_argument("--csv", type=Path, default=ROOT / "Qualified_Jobs.csv")
    sub.add_parser("list", help="List the local application queue")
    prep = sub.add_parser("prepare", help="Generate a job-specific resume and mark ready for review")
    prep.add_argument("job_id", type=int)
    prep.add_argument("--profile", type=Path, default=PROFILE_DEFAULT)
    prep.add_argument("--resume-dir", type=Path, default=RESUME_DIR_DEFAULT)
    openp = sub.add_parser("open", help="Open a job page for the human application step")
    openp.add_argument("job_id", type=int)
    sub.add_parser("counts", help="Show counts by state")
    args = parser.parse_args()

    try:
        with connect(args.db) as conn:
            if args.command == "import":
                inserted, updated = import_csv(conn, args.csv)
                print(f"Imported/updated leads. New: {inserted}; existing refreshed: {updated}.")
            elif args.command == "list":
                rows = conn.execute("SELECT id,title,company,score,status,resume_path,canonical_url FROM jobs ORDER BY score DESC,id").fetchall()
                for row in rows:
                    print(f"#{row['id']} [{row['status']}] score={row['score']} | {row['company']} — {row['title']} | resume={row['resume_path'] or '-'} | {row['canonical_url']}")
            elif args.command == "counts":
                for row in conn.execute("SELECT status,COUNT(*) AS n FROM jobs GROUP BY status ORDER BY status"):
                    print(f"{row['status']}: {row['n']}")
            elif args.command == "prepare":
                row = conn.execute("SELECT * FROM jobs WHERE id=?", (args.job_id,)).fetchone()
                if not row:
                    print(f"Unknown job id {args.job_id}", file=sys.stderr)
                    return 2
                if row["status"] not in {"DISCOVERED", "QUALIFIED", "PREPARED", "READY_FOR_REVIEW"}:
                    print(f"Cannot prepare a resume from state {row['status']}", file=sys.stderr)
                    return 2
                if not args.profile.exists():
                    print(f"Candidate profile not found: {args.profile}", file=sys.stderr)
                    return 2
                profile = json.loads(args.profile.read_text(encoding="utf-8"))
                pdf = build_resume(row, profile, args.resume_dir)
                conn.execute("UPDATE jobs SET status='PREPARED',resume_path=?,updated_at=? WHERE id=?", (str(pdf),now(),args.job_id))
                conn.execute("INSERT INTO application_events(job_id,from_status,to_status,note,created_at) VALUES(?,?,?,?,?)",
                             (args.job_id,row["status"],"PREPARED",f"Resume generated: {pdf}",now()))
                conn.commit()
                print(f"Resume prepared: {pdf}")
                print("Review every factual claim and the job requirements before submitting.")
            elif args.command == "open":
                row = conn.execute("SELECT * FROM jobs WHERE id=?", (args.job_id,)).fetchone()
                if not row:
                    print(f"Unknown job id {args.job_id}", file=sys.stderr)
                    return 2
                if not row["resume_path"] or not Path(row["resume_path"]).exists():
                    print("Prepare a job-specific resume first: python application_queue.py prepare <job_id>", file=sys.stderr)
                    return 2
                print(f"Opening {row['canonical_url']}")
                print(f"Resume to upload: {row['resume_path']}")
                print("Complete the employer's questions yourself. Do not submit until you verify the resume and every answer.")
                webbrowser.open(row["canonical_url"])
            return 0
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
