# AIM1000

**AIM1000 is a local-first job-search operations tool** that turns job-lead CSVs into a qualified queue, candidate-fact-based resumes, and a local review dashboard.

The release foundation is designed around safe throughput: up to 1,000 jobs scored and resumes prepared per batch, with duplicate protection and audit history. It does not promise 1,000 submissions and does not submit forms on a user's behalf.

## Quick start

See [AIM1000 Quick Start](AIM1000_QUICKSTART.md). After creating and reviewing your private `candidate_profile.json`, run:

```bash
python application_queue.py profile-check --profile candidate_profile.json
python aim1000_pipeline.py --input Sniper_Hourly_Leads.csv --profile candidate_profile.json --max-jobs 1000 --min-score 25
```

Outputs include `Qualified_Jobs.csv`, `aim1000.db`, role-specific PDFs under `resumes/`, and `Mission_Control.html`. These contain private application data and are ignored by Git.

## Components

- `job_filter_agent.py`: transparent heuristic scoring, reasons, URL normalization and deduplication.
- `application_queue.py`: local SQLite state, status history, candidate-profile validation, and PDF generation.
- `aim1000_pipeline.py`: bounded end-to-end batch preparation and the local Mission Control dashboard.
- `application_executor.py`: visible-browser helper for LinkedIn and selected employer portals. Fills an allowlist of factual fields and stops before submission.
- `tests/`: unit tests for scoring, queue transitions, profile validation, and guarded autofill.
- `.github/workflows/test.yml`: CI unit-test workflow.

## Security and accuracy model

1. Candidate facts must be reviewed in a private JSON profile before PDF generation.
2. Placeholder content blocks the workflow.
3. Generated documents use supplied facts; the system must not invent credentials, dates, metrics, or employment history.
4. Unknown questions and employer declarations stay with the candidate.
5. No automatic Apply/Submit, CAPTCHA bypass, credential storage, or hidden browser activity.
6. Each prepared item is tracked locally; opening a page is not considered an application submission.

The job score is a rough prioritization aid, not a claim that the candidate is qualified. Check platform terms, access restrictions and rate limits before using automation.

## Development

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Do not commit `candidate_profile.json`, lead CSVs, generated PDFs, `aim1000.db`, or Mission Control output.
