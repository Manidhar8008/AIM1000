# AIM1000 Quick Start

AIM1000 prepares a role-specific resume and keeps a local application queue. The current guided workflow opens the employer's job page for you; it does not silently submit applications or answer employer declarations.

## 1. Install
```bash
python -m venv .venv
# Linux/macOS/Termux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## 2. Create your candidate profile
Copy `candidate_profile.example.json` to `candidate_profile.json`. Replace all placeholder bullets with verified experience, dates, skills, education, and measurable results. Remove any skill or claim you cannot substantiate. Do not commit the private profile to a public repository.

## 3. Create a ranked lead file
If the scraper produces `Sniper_Hourly_Leads.csv`, run:
```bash
python job_filter_agent.py --input Sniper_Hourly_Leads.csv --output Qualified_Jobs.csv --min-score 25
``

## 4. Import into SQLite
```bash
python application_queue.py import --csv Qualified_Jobs.csv
python application_queue.py list
python application_queue.py counts
``
The default database is `aim1000.db` in the repository folder. Keep this database local; it contains personal job-search records.

## 5. Prepare a tailored resume
Use the numeric ID shown by `list`:
```bash
python application_queue.py prepare 1 --profile candidate_profile.json
``
A PDF is written under `resumes/`. Tailoring reorders candidate-provided skills against the job description and includes profile-provided experience/projects. It does not invent experience or metrics. Review the PDF before every use.

## 6. Apply with a human review gate
```bash
python application_queue.py open 1
``
This opens the job page and prints the exact resume path. Upload the PDF, review the employer's questions and declarations, and submit yourself. A future site-specific browser adapter can fill safe, factual fields, but must stop before final submission until you approve the application.

## Tests
```bash
python -m unittest discover -s tests
``

## Important limits
- Scraping selectors and job-board access can change; respect each platform's terms and rate limits.
- Never automate answers to legal eligibility, work authorization, disability, veteran status, criminal history, or other declarations without explicit review.
- Do not store account passwords, session cookies, or API secrets in the repository.
## 7. Visible-browser autofill (LinkedIn and selected career portals)
After preparing a role-specific resume, run:
```bash
python application_executor.py 1 --profile candidate_profile.json --wait
```
This opens a visible browser, attempts to attach the PDF and fills only recognized factual fields from your profile. It never clicks Apply, Next, Save, or Submit. Review the page and submit manually only after explicit approval. Sensitive declarations and unrecognized questions are left for you.
