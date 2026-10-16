import unittest

from job_filter_agent import canonical_url, find_value, score_job


class JobFilterAgentTests(unittest.TestCase):
    def test_header_aliases_are_case_and_space_insensitive(self):
        row = {"Job Title": "Python Engineer", "Company Name": "Example Ltd"}
        self.assertEqual(find_value(row, ("title", "job title")), "Python Engineer")
        self.assertEqual(find_value(row, ("company", "company name")), "Example Ltd")

    def test_tracking_parameters_are_removed_from_urls(self):
        self.assertEqual(
            canonical_url("https://www.example.com/jobs/123/?utm_source=feed#apply"),
            "https://example.com/jobs/123",
        )

    def test_query_job_identifier_survives_tracking_cleanup(self):
        self.assertEqual(
            canonical_url("https://jobs.example.org/role?gh_jid=123&utm_campaign=test&trackingId=x"),
            "https://jobs.example.org/role?gh_jid=123",
        )
        self.assertEqual(canonical_url("not a URL"), "")

    def test_rows_without_identifiers_are_not_all_collapsed(self):
        import csv
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from job_filter_agent import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "in.csv", root / "out.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Job Title", "Company", "Apply Link"])
                writer.writeheader()
                writer.writerow({"Job Title": "", "Company": "", "Apply Link": ""})
                writer.writerow({"Job Title": "", "Company": "", "Apply Link": ""})
            with patch("sys.argv", ["job_filter_agent.py", "--input", str(source), "--output", str(destination)]):
                self.assertEqual(main(), 0)
            with destination.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)

    def test_relevant_job_scores_and_explains_signals(self):
        row = {
            "Job Title": "Python Machine Learning Engineer",
            "Company": "Example Ltd",
            "Location": "Remote India",
            "Job URL": "https://example.com/jobs/1",
            "Description": "Build AI automation and FastAPI services",
        }
        score, reason = score_job(row)
        self.assertGreaterEqual(score, 25)
        self.assertIn("python", reason)
        self.assertIn("company", reason)

    def test_unpaid_role_receives_penalty(self):
        base = {"Job Title": "Python Engineer", "Company": "Example"}
        unpaid = {**base, "Description": "Unpaid Python Engineer"}
        self.assertLess(score_job(unpaid)[0], score_job(base)[0])


if __name__ == "__main__":
    unittest.main()
