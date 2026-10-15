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
