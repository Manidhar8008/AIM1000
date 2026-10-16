import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from argparse import Namespace

from aim1000_pipeline import run as run_pipeline


class PipelineIntegrationTests(unittest.TestCase):
    def test_pipeline_prepares_resume_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leads = root / "leads.csv"
            profile_path = root / "candidate_profile.json"
            output_csv = root / "Qualified_Jobs.csv"
            db_path = root / "aim1000.db"
            resumes = root / "resumes"
            dashboard = root / "Mission_Control.html"
            profile = {
                "profile_reviewed": True,
                "candidate_name": "Test Candidate",
                "email": "candidate@acme.io",
                "phone": "",
                "location": "Remote, India",
                "linkedin_url": "",
                "github_url": "",
                "portfolio_url": "",
                "headline": "Python Engineer",
                "summary": "Candidate-approved summary.",
                "skills": ["Python", "SQL"],
                "experience": [{
                    "company": "Acme",
                    "title": "Developer",
                    "dates": "2020-2022",
                    "bullets": ["Built a Python workflow and documented the outcome."]
                }],
                "projects": [],
                "education": [],
                "certifications": [],
                "job_preferences": {
                    "target_roles": ["Python Engineer"],
                    "preferred_locations": ["India"],
                    "remote_only": True
                }
            }
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            with leads.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "Job Title", "Company", "Location", "Apply Link", "Description"
                ])
                writer.writeheader()
                writer.writerow({
                    "Job Title": "Python Engineer",
                    "Company": "Acme",
                    "Location": "Remote India",
                    "Apply Link": "https://jobs.acme.io/role?job_id=123&utm_source=test",
                    "Description": "Build Python backend services with SQL in a remote team."
                })

            args = Namespace(
                input=leads, qualified_csv=output_csv, profile=profile_path,
                db=db_path, resume_dir=resumes, dashboard=dashboard,
                max_jobs=1000, min_score=25, timeout=60
            )
            self.assertEqual(run_pipeline(args), 0)
            self.assertTrue(dashboard.is_file())
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
                status, resume_path = conn.execute("SELECT status,resume_path FROM jobs").fetchone()
                self.assertEqual(status, "PREPARED")
                self.assertTrue(Path(resume_path).is_file())

            # Re-importing the same lead should not create a second row or regenerate it.
            self.assertEqual(run_pipeline(args), 0)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM application_events").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
