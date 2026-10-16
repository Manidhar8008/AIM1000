# AIM1000 Quick Start

AIM1000 turns a job-lead CSV into a deduplicated, scored review queue, role-specific PDF resumes, and a local Mission Control dashboard. It does **not** submit applications automatically.

## 1. Install on your laptop

Use Python 3.11 or 3.12.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For macOS/Linux, create and activate the environment with `python -m venv .venv` and `source .venv/bin/activate`.

## 2. Build your private candidate profile

```powershell
Copy-Item candidate_profile.example.json candidate_profile.json
code candidate_profile.json
```

Enter your real contact details, employment dates, education, verified skills, and work/project bullets. In `job_preferences`, add the exact role titles you want, preferred locations, and whether remote-only jobs are required. Remove anything you cannot support. Do not add invented metrics, qualifications, employment dates, or experience. Set `"profile_reviewed": true` only after checking every field.

The private profile, database, lead files, generated resumes, and dashboard are excluded from Git by `.gitignore`. Keep them local and never commit them.

Check the profile before processing jobs:

```powershell
python application_queue.py profile-check --profile candidate_profile.json
```

## 3. Run the batch pipeline

Place your job-lead CSV at `Sniper_Hourly_Leads.csv` (or pass a different path). It should contain a title, company, and job URL, with a description/snippet when available.

```powershell
python aim1000_pipeline.py --input Sniper_Hourly_Leads.csv --profile candidate_profile.json --max-jobs 1000 --min-score 25
```

This single command:
1. scores and deduplicates leads;
2. excludes rows marked `LOW_PRIORITY`;
3. imports qualified URLs idempotently into local SQLite;
4. creates up to 1,000 job-specific PDFs using only profile facts;
5. updates state history and writes `Mission_Control.html`.

Open `Mission_Control.html` in your browser to review each job and its PDF. Re-running the pipeline won't create duplicate database rows or re-prepare jobs that are already prepared. A job with a failed PDF stays in the queue for investigation/retry.

Useful commands:

```powershell
python application_queue.py list
python application_queue.py counts
python -m unittest discover -s tests -v
```

## 4. Use the visible-browser helper

After reviewing a prepared PDF, the helper can open a stored job and fill limited factual fields:

```powershell
python application_executor.py 1 --profile candidate_profile.json --wait
```

Sign in yourself. It pauses on visible password/login pages, only attaches a PDF to an explicitly labeled resume/CV upload, preserves fields already populated by the site, and leaves unknown or sensitive questions untouched.

## Approval and compliance boundary

- The helper never clicks **Apply**, **Next**, **Save**, or **Submit**. You review and submit each application yourself.
- Work authorization, visa/sponsorship, demographics, criminal history, salary expectations, notice period, experience-duration questions, and other declarations require your direct review.
- Don't bypass CAPTCHA, bot checks, account controls, or site limits. Use data collection and browser assistance only where permitted by the relevant job site.
- A score is a heuristic, not a guarantee of qualification. Read the description and reject mismatches before applying.
- A prepared resume is not a submitted application. Record actual outcomes honestly.
- Do not run the legacy autopilot / legacy AI resume scripts; they are disabled because they loop indefinitely or can generate unsupported resume claims.

## Batch definition

The `--max-jobs` cap is 1,000 prepared resumes per run. Larger lead sets can be processed in separate batches. This is not a promise of 1,000 applications submitted. Quality, truthful answers, employer requirements, and human approval take precedence over throughput.
