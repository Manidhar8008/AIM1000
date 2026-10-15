# AIM1000 Application Executor

## Scope
The visible-browser executor is an assistant, not an unattended submitter. It opens a job already stored in SQLite, detects LinkedIn and selected career-portal hosts, attaches the per-job PDF when a visible file input is available, and fills a small allowlist of factual fields from the candidate's private profile.

Supported host families: LinkedIn, Greenhouse, Lever, Workday, and Ashby. All other hosts open in review-only mode.

## Run
1. Prepare the resume:
   ```bash
   python application_queue.py prepare 1 --profile candidate_profile.json
   ``
2. Run the visible browser:
   ```bash
   python application_executor.py 1 --profile candidate_profile.json --wait
   ``
3. Sign in yourself, review every filled field and attached PDF, complete any employer-specific questions, and submit manually only after explicit approval.

Use `--browser firefox` to choose Firefox. The browser session is not persisted by this tool; sign in yourself each run.

## Safety and limitations
- It never clicks Apply, Next, Save, or Submit.
- It does not bypass CAPTCHAs, bot checks, queues, or access controls.
- It does not answer work authorization, sponsorship, demographic, criminal-history, salary, experience-duration, or other sensitive/declarative questions.
- It does not overwrite fields already populated by the site.
- DOM labels vary by employer; some file inputs or fields may not be detected. Inspect the page and complete missing fields manually.
- Site terms and automation policies vary. Use only where permitted and stop if the site blocks automation.
- The current CLI does not update a job to SUBMITTED automatically. Record outcomes separately after the human action; do not treat opening a page as a successful application.
- No credentials, cookies, or session tokens are stored by this tool.

## Tests
```bash
python -m unittest discover -s tests -v
``
