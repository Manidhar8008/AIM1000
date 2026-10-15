#!/usr/bin/env python3
"""AIM1000 job qualification and deduplication stage.

Reads scraped job leads, assigns a transparent heuristic score, removes duplicates,
and writes a review queue. This module never submits applications or contacts employers.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

TITLE_KEYS = ("title", "job title", "position", "role", "designation")
COMPANY_KEYS = ("company", "company name", "employer", "organization", "organisation")
LOCATION_KEYS = ("location", "job location", "place")
URL_KEYS = ("url", "job url", "link", "apply link", "job link", "job_url")
DESCRIPTION_KEYS = ("description", "job description", "summary", "snippet", "details")

POSITIVE_TERMS = {
    "python": 12, "machine learning": 12, " ml ": 5, "artificial intelligence": 12,
    " ai ": 5, "automation": 8, "data engineer": 8, "software engineer": 8,
    "backend": 6, "fastapi": 8, "sql": 4, "postgresql": 5, "llm": 8,
    "generative ai": 10, "cloud": 4, "devops": 4, "mlops": 8,
    "analyst": 3, "remote": 5, "hybrid": 2,
}
NEGATIVE_TERMS = {
    "unpaid": -18, "commission only": -20, "internship": -8,
    "sales representative": -8, "business development": -5,
    "training fee": -30, "pay to apply": -30,
}


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def find_value(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    normalized = {normalized_header(k): (v or "").strip() for k, v in row.items()}
    for alias in aliases:
        key = normalized_header(alias)
        if normalized.get(key):
            return normalized[key]
    for key, value in normalized.items():
        if value and any(normalized_header(alias) in key for alias in aliases):
            return value
    return ""


def canonical_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            return value.rstrip("/").lower()
        host = parsed.netloc.lower().removeprefix("www.")
        path = re.sub(r"/+$", "", parsed.path)
        # Drop tracking parameters and fragments for stable deduplication.
        return urlunparse((parsed.scheme.lower(), host, path, "", "", ""))
    except ValueError:
        return value.rstrip("/").lower()


def score_job(row: dict[str, str]) -> tuple[int, str]:
    title = find_value(row, TITLE_KEYS)
    description = find_value(row, DESCRIPTION_KEYS)
    location = find_value(row, LOCATION_KEYS)
    text = f" {title} {description} {location} ".lower()
    score = 0
    reasons: list[str] = []

    for term, weight in POSITIVE_TERMS.items():
        if term in text:
            score += weight
            reasons.append(f"+{term.strip()}:{weight}")
    for term, weight in NEGATIVE_TERMS.items():
        if term in text:
            score += weight
            reasons.append(f"{term}:{weight}")

    if title:
        score += 5
        reasons.append("+title:5")
    if find_value(row, COMPANY_KEYS):
        score += 3
        reasons.append("+company:3")
    if find_value(row, URL_KEYS):
        score += 3
        reasons.append("+url:3")

    return max(0, min(100, score)), "; ".join(reasons) or "No matching signals"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="Sniper_Hourly_Leads.csv", help="Input leads CSV")
    parser.add_argument("--output", default="Qualified_Jobs.csv", help="Output review queue CSV")
    parser.add_argument("--min-score", type=int, default=25, help="Minimum score to mark QUALIFIED (default: 25)")
    args = parser.parse_args()

    source, destination = Path(args.input), Path(args.output)
    if not source.exists():
        print(f"ERROR: input file not found: {source}", file=sys.stderr)
        return 2
    if source.resolve() == destination.resolve():
        print("ERROR: input and output paths must differ.", file=sys.stderr)
        return 2

    with source.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            print("ERROR: input CSV has no header row.", file=sys.stderr)
            return 2
        original_fields = list(reader.fieldnames)
        rows = list(reader)

    output_fields = original_fields + [
        field for field in ("qualification_score", "qualification_reason", "qualification_status")
        if field not in original_fields
    ]
    seen: set[str] = set()
    output_rows: list[dict[str, str]] = []
    duplicate_count = 0

    for row in rows:
        url = canonical_url(find_value(row, URL_KEYS))
        title = find_value(row, TITLE_KEYS).lower()
        company = find_value(row, COMPANY_KEYS).lower()
        dedupe_key = f"url:{url}" if url else f"title-company:{re.sub(r'\\s+', ' ', title).strip()}|{re.sub(r'\\s+', ' ', company).strip()}"
        if dedupe_key.strip("|") and dedupe_key in seen:
            duplicate_count += 1
            continue
        if dedupe_key.strip("|"):
            seen.add(dedupe_key)

        score, reason = score_job(row)
        row["qualification_score"] = str(score)
        row["qualification_reason"] = reason
        row["qualification_status"] = "QUALIFIED_REVIEW" if score >= args.min_score else "LOW_PRIORITY"
        output_rows.append(row)

    output_rows.sort(key=lambda item: int(item.get("qualification_score", "0")), reverse=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)

    qualified = sum(row["qualification_status"] == "QUALIFIED_REVIEW" for row in output_rows)
    print(f"Input rows: {len(rows)}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Unique jobs written: {len(output_rows)}")
    print(f"Qualified for human review: {qualified}")
    print(f"Output: {destination}")
    print("Safety: this stage does not apply, message recruiters, or submit forms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
