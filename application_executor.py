#!/usr/bin/env python3
"""AIM1000 visible-browser application assistant.

Opens an existing job from the SQLite queue, attaches a job-specific resume where
a supported file input is present, and fills only low-risk factual fields sourced
from the candidate profile. It never clicks Submit/Apply/Next, answers sensitive
questions, bypasses CAPTCHAs, or hides browser automation. The user reviews and
submits manually.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from application_queue import DB_DEFAULT, PROFILE_DEFAULT, connect

# Labels are intentionally conservative. Never infer eligibility or declarations.
FIELD_RULES = (
    (("email", "e-mail"), ("email",)),
    (("phone", "mobile", "telephone"), ("phone",)),
    (("first name", "given name", "firstname"), ("first_name",)),
    (("last name", "family name", "surname", "lastname"), ("last_name",)),
    (("linkedin profile", "linkedin url", "linkedin.com"), ("linkedin_url",)),
    (("github profile", "github url", "github.com"), ("github_url",)),
    (("portfolio", "personal website", "website url"), ("portfolio_url",)),
    (("city", "current city"), ("city",)),
    (("postal code", "zip code", "pincode", "pin code"), ("postal_code",)),
)

SENSITIVE_TERMS = (
    "work authorization", "sponsorship", "visa", "disability", "veteran",
    "gender", "race", "ethnicity", "date of birth", "criminal", "conviction",
    "salary expectation", "expected salary", "notice period", "years of experience",
    "legally authorized", "require sponsorship",
)


def safe_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def infer_value(label: str, profile: dict) -> tuple[str | None, str]:
    """Return (value, reason); unknown or sensitive fields are left untouched."""
    label = safe_text(label)
    if any(term in label for term in SENSITIVE_TERMS):
        return None, "sensitive_or_declaration"
    for phrases, keys in FIELD_RULES:
        if any(phrase in label for phrase in phrases):
            for key in keys:
                value = str(profile.get(key, "") or "").strip()
                if value:
                    return value, "profile_match"
            return None, "profile_value_missing"
    return None, "unrecognized_field"


def supported_site(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        return "linkedin"
    if any(host == domain or host.endswith("." + domain) for domain in
           ("greenhouse.io", "lever.co", "myworkdayjobs.com", "workday.com", "ashbyhq.com")):
        return "career_portal"
    return "generic_review_only"


def field_label(element) -> str:
    parts = [
        element.get_attribute("aria-label") or "",
        element.get_attribute("placeholder") or "",
        element.get_attribute("name") or "",
        element.get_attribute("id") or "",
        element.get_attribute("autocomplete") or "",
    ]
    element_id = element.get_attribute("id")
    if element_id:
        try:
            labels = element._parent.find_elements("css selector", f'label[for="{element_id}"]')
            parts.extend(label.text or "" for label in labels)
        except Exception:
            pass
    try:
        parent_label = element.find_element("xpath", "./ancestor::label[1]")
        parts.append(parent_label.text or "")
    except Exception:
        pass
    return " ".join(parts)


def run(args) -> int:
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError:
        print("Selenium is required. Install with: pip install -r requirements.txt", file=sys.stderr)
        return 2

    profile_path = args.profile
    if not profile_path.exists():
        print(f"Candidate profile not found: {profile_path}", file=sys.stderr)
        return 2
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read candidate profile: {exc}", file=sys.stderr)
        return 2

    with connect(args.db) as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id=?", (args.job_id,)).fetchone()
        if not job:
            print(f"Unknown job id: {args.job_id}", file=sys.stderr)
            return 2
        if not job["resume_path"] or not Path(job["resume_path"]).is_file():
            print("Prepare a job-specific resume first: python application_queue.py prepare <job_id>", file=sys.stderr)
            return 2
        url = job["canonical_url"]
        resume = str(Path(job["resume_path"]).resolve())

    site = supported_site(url)
    print(f"Job: {job['title']} — {job['company']}")
    print(f"Detected adapter: {site}")
    if site == "generic_review_only":
        print("This host is not in the supported adapter list. Opening for manual review only.")
    print("Browser is visible. Sign in yourself if needed. Do not share or store passwords/cookies.")
    options = webdriver.ChromeOptions()
    if args.browser == "chrome":
        driver = webdriver.Chrome(options=options)
    else:
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        driver = webdriver.Firefox(options=FirefoxOptions())

    filled, skipped, attached = [], [], False
    try:
        driver.get(url)
        WebDriverWait(driver, args.timeout).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )
        # Never click buttons or submit. This assistant only fills a limited allowlist.
        if site != "generic_review_only":
            for element in driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), textarea"):
                try:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    typ = (element.get_attribute("type") or "text").lower()
                    label = field_label(element)
                    if typ == "file":
                        element.send_keys(resume)
                        attached = True
                        filled.append("resume attachment")
                        continue
                    if typ in {"checkbox", "radio", "submit", "button", "password", "file"}:
                        continue
                    value, reason = infer_value(label, profile)
                    if value is None:
                        if reason in {"sensitive_or_declaration", "unrecognized_field"}:
                            skipped.append(f"{label or '(unlabelled field)'} [{reason}]")
                        continue
                    current = (element.get_attribute("value") or "").strip()
                    if current:
                        # Preserve user/site prefilled values; don't silently overwrite.
                        skipped.append(f"{label} [already populated]")
                        continue
                    element.clear()
                    element.send_keys(value)
                    filled.append(label)
                except Exception as exc:
                    skipped.append(f"field interaction failed: {type(exc).__name__}")
        print("\n=== REVIEW CHECKLIST ===")
        print(f"Fields filled: {len(filled)}")
        for item in filled:
            print(f"  FILLED: {item}")
        print(f"Fields left for review: {len(skipped)}")
        for item in skipped[:40]:
            print(f"  REVIEW: {item}")
        print(f"Resume attached automatically: {'yes' if attached else 'no — attach manually if needed'}")
        print("No Apply, Next, Save, or Submit control was clicked.")
        print("Review every field, the resume, required declarations, and employer-specific questions.")
        print("Submit manually only when you explicitly approve this application.")
        if args.wait:
            input("\nPress Enter after you have reviewed/submitted (or close the browser) to exit...")
    except KeyboardInterrupt:
        print("\nInterrupted; no submit action was performed.")
    finally:
        if not args.keep_browser:
            driver.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_id", type=int)
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    parser.add_argument("--profile", type=Path, default=PROFILE_DEFAULT)
    parser.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--wait", action="store_true", help="Wait for Enter before closing browser")
    parser.add_argument("--keep-browser", action="store_true", help="Leave browser open after script exits")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
