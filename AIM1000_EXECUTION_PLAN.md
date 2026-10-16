# AIM1000 — Product Execution and Release Plan

## Product definition
AIM1000 is a local-first job-search workflow for ingesting job leads, prioritizing them against a candidate-controlled profile, preventing duplicates, creating role-specific PDF resumes from verified facts, and managing review from a local Mission Control dashboard.

The throughput target is up to 1,000 **prepared opportunities per batch**, not 1,000 automatic submissions. The candidate remains accountable for the truth of resume claims and employer answers.

## Legacy repository findings
The original repository contained LinkedIn Selenium scrapers, multiple resume generators, HTML trackers, and managers that repeatedly executed shell commands. The legacy generators included a fixed skill list or AI-written summary/project claims that were not grounded in verified candidate facts; two managers ran in unbounded loops. These entry points have been disabled in this branch. Their earlier versions remain available in Git history. Use the bounded pipeline described in `AIM1000_QUICKSTART.md`.

## Current release implementation
- `job_filter_agent.py`: heuristic score with reason codes, URL identity preservation, tracking-query cleanup, duplicate filtering, and malformed-row handling.
- `application_queue.py`: SQLite local queue, transition/event log, role-specific PDF generation, profile validation, and profile-check command.
- `aim1000_pipeline.py`: single-command bounded batch that validates the candidate profile, scores and deduplicates a CSV, imports unique qualified leads, creates at most 1,000 PDFs, and writes `Mission_Control.html`.
- `application_executor.py`: visible-browser assistant for selected job hosts. It fills only recognized factual fields, pauses on visible password fields, attaches files only to clearly labeled resume/CV inputs, and never submits.
- `.gitignore`: excludes private candidate JSON, local DBs, source/output CSVs, logs, generated resumes, and dashboard output.
- `tests/`: unit tests for the most important logic and previously missed safety regressions.
- `.github/workflows/test.yml`: CI test workflow.

## Batch workflow
```bash
python application_queue.py profile-check --profile candidate_profile.json
python aim1000_pipeline.py --input Sniper_Hourly_Leads.csv --profile candidate_profile.json --max-jobs 1000 --min-score 25
python application_queue.py list
python application_queue.py counts
python -m unittest discover -s tests -v
```

## Non-negotiable release guardrails
1. Candidate facts and claims must be explicitly reviewed before generation; placeholder text blocks the run.
2. Never invent employment dates, education, metrics, skills, certifications, or accomplishments.
3. Keep employer-specific declarations and unknown questions under human control.
4. Don't treat opening a page or preparing a PDF as a successful application.
5. No automatic Submit, CAPTCHA bypass, credential storage, or hidden browser automation.
6. Respect each job site's terms, access controls, and rate limits.

## Release acceptance
- One bounded command processes an existing CSV into a deduplicated queue, PDFs, and dashboard.
- Re-running the same lead set is idempotent at the database URL level.
- Private candidate/job-search artifacts are ignored by Git.
- Unit tests and GitHub Actions pass on the final branch head.

## Known limitations before production/SaaS
- No browser end-to-end run has been validated on the user's laptop.
- Board selectors change and site-specific autofill must be manually checked; unsupported hosts remain manual-only.
- Qualification weights are heuristics and currently need candidate preference/résumé-aware calibration.
- Submission, rejection, interview, and follow-up outcomes still require a deliberate tracking action; no application is silently auto-submitted.
- For a hosted multi-user SaaS, add authentication, tenant isolation, encrypted storage, deletion/export controls, job-provider integrations, job-source terms review, observability, and deployment security before hosting private candidate profiles.
