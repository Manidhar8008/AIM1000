# AIM1000 Application Executor

## Scope
The visible-browser helper opens one job already stored in SQLite, attaches the prepared PDF only when a field is explicitly labeled as a resume/CV upload, and fills a small allowlist of factual fields from the candidate-reviewed local profile.

Supported host families are LinkedIn, Greenhouse, Lever, Workday, and Ashby. Other hosts open in review-only mode. Actual DOM labels and site terms vary, so inspect every page.

## Run
1. Prepare candidate facts and validate them:
   ```bash
   python application_queue.py profile-check --profile candidate_profile.json
   ```
2. Run the batch:
   ```bash
   python aim1000_pipeline.py --input Sniper_Hourly_Leads.csv --profile candidate_profile.json --max-jobs 1000
   ```
3. Review the dashboard and the corresponding PDF.
4. Run the helper for a single queue ID:
   ```bash
   python application_executor.py 1 --profile candidate_profile.json --wait
   ```

Use `--browser firefox` to choose Firefox.

## Guardrails
- Never clicks Apply, Next, Save, or Submit.
- Pauses autofill if a visible password field appears; sign in or complete account setup manually.
- Attaches a PDF only when the input label clearly identifies resume/CV; cover-letter, transcript, and unlabeled file inputs are left alone.
- Does not overwrite fields already populated by the site.
- Leaves employer declarations, eligibility, sponsorship, demographics, salary expectations, notice period, experience-duration questions, and unknown fields for direct human review.
- Does not bypass CAPTCHAs, bot checks, queues, access controls, or site limits.
- Does not store account passwords, cookies, or session tokens.
- Does not automatically mark an application as submitted. A prepared resume or opened job page is not proof of submission.

## Release validation still required
GitHub Actions unit tests cover pure logic only. Before trusting browser autofill, test manually with a non-sensitive sample application on each permitted target site, verify every field and upload, and stop if a site blocks automation.
