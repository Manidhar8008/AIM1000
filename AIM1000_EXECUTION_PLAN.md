# AIM1000 — Execution Foundation

## Product objective
Turn the existing job discovery and resume-generation scripts into a reliable, reviewable job-application pipeline. The target is throughput (up to 1,000 qualified opportunities), not blind mass submission.

## Repository baseline observed
- `sniper_bot_final.py` and `turbo_sniper.py`: Selenium-based LinkedIn job discovery.
- `autopilot_manager.py`: repeats scraping and resume generation on a one-hour loop using `os.system`.
- `generate_resumes.py`: reads `Sniper_Hourly_Leads.csv` and produces resume artifacts / Mission Control output.
- `requirements.txt`: Selenium, webdriver-manager, pandas, openpyxl.
- `Mission_Control.html`: static HTML tracker with links to apply and download artifacts.
- Latest repository commit returned by GitHub connector: `AI auto JOB helper` (2025-12-04).

## Main gaps
1. No durable application/job state store.
2. No stable deduplication and qualification stage before resume generation.
3. No explicit state machine, retry policy, or per-job audit log.
4. Scrape/generate orchestration uses shell calls and an infinite loop without structured exit codes or run history.
5. No reliable application submission status model.
6. The dashboard is a generated HTML snapshot, not a live queue.

## Implemented in this branch
### `job_filter_agent.py`
- Reads the current lead CSV format without requiring a database migration.
- Finds common title/company/location/URL/description header variants.
- Applies transparent, editable heuristic scoring and reason codes.
- Deduplicates by canonical URL, falling back to normalized title + company.
- Writes `Qualified_Jobs.csv`, sorted by score.
- Labels rows `QUALIFIED_REVIEW` or `LOW_PRIORITY`.
- Does **not** apply to jobs, send messages, or submit forms.

Run:
```bash
python job_filter_agent.py --input Sniper_Hourly_Leads.csv --output Qualified_Jobs.csv --min-score 25
```

## Recommended state model
`DISCOVERED → DEDUPED → QUALIFIED → PREPARED → READY_FOR_REVIEW → APPLYING → SUBMITTED`

Exception states: `NEEDS_HUMAN`, `FAILED_RETRYABLE`, `REJECTED`, `FOLLOW_UP_DUE`.

Submission must be explicit and auditable. A human-review gate should remain for employer-specific questions, consent, declarations, salary expectations, and any form that is not confidently mapped.

## Next implementation sequence
1. Add tests for header variants, duplicate URLs, missing URLs, empty CSVs, scoring, and malformed rows.
2. Introduce SQLite as the local-first source of truth (`jobs`, `applications`, `artifacts`, `execution_logs`, `candidate_profile`, `application_answers`).
3. Add a CLI orchestrator using subprocess argument arrays, timeouts, exit-code checks, and structured logs; remove the unbounded `os.system` loop.
4. Generate per-job resume artifacts only for qualified jobs; retain a manifest linking job ID → resume path → score → status.
5. Upgrade Mission Control to show queue counts, top scored jobs, missing information, artifact readiness, and status transitions.
6. Add browser automation adapters only after stable selectors, safe retries, duplicate-submit protection, and a human confirmation step are in place.

## Acceptance criteria for the first usable slice
- One command turns a scraped CSV into a deduplicated, scored review queue.
- Re-running it does not produce duplicate jobs in the output.
- Every scored row contains a human-readable reason.
- Missing input fails with a clear non-zero exit code.
- No application is submitted automatically by this stage.
