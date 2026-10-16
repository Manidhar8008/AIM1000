#!/usr/bin/env python3
"""Legacy entry point disabled in favor of the bounded AIM1000 batch pipeline."""

def main() -> int:
    print("SAFETY STOP: legacy autopilot is disabled.")
    print("It ran unbounded scrape/generate cycles and could invoke legacy resume generators.")
    print("Use: python aim1000_pipeline.py --input Sniper_Hourly_Leads.csv --profile candidate_profile.json --max-jobs 1000")
    print("AIM1000 will prepare resumes for review; it will not submit applications.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
