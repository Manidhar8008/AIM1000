#!/usr/bin/env python3
"""Legacy scraping/resume orchestration disabled; see AIM1000_QUICKSTART.md."""

def main() -> int:
    print("SAFETY STOP: ai_factory_v2.py is retired. It ran repeated shell commands in an unbounded loop.")
    print("Use aim1000_pipeline.py with a candidate-reviewed profile. The new flow does not invent resume claims.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
