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
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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


TRACKING_QUERY_KEYS = {
    "refid", "trackingid", "trk", "ebp", "source", "campaign",
    "gclid", "fbclid", "mc_cid", "mc_eid", "li_fat_id",
}


def canonical_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return ""
        if parsed.username or parsed.password:
            return ""
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower().removeprefix("www.")
        port = parsed.port
        if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
            hostname = f"{hostname}:{port}"
        path = re.sub(r"/+$", "", parsed.path) or "/"
        query = [
            (key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
        ]
        return urlunparse((scheme, hostname, path, "", urlencode(sorted(query)), ""))
    except ValueError:
        return ""


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

    if not 0 <= args.min_score <= 100:
        print("ERROR: --min-score must be between 0 and 100.", file=sys.stderr)
        return 2
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
        title_key = re.sub(r"\s+", " ", title).strip()
        company_key = re.sub(r"\s+", " ", company).strip()
        if url:
            dedupe_key = f"url:{url}"
        elif title_key or company_key:
            dedupe_key = f"title-company:{title_key}|{company_key}"
        else:
            dedupe_key = ""
        if dedupe_key and dedupe_key in seen:
            duplicate_count += 1
            continue
        if dedupe_key:
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
