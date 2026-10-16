#!/usr/bin/env python3
"""Legacy infinite-loop manager disabled for safety."""

def main() -> int:
    print("SAFETY STOP: manager_bot.py is retired; it ran endless scrape and AI-resume cycles.")
    print("Use the bounded, reviewed batch pipeline documented in AIM1000_QUICKSTART.md.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
