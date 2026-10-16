import unittest

from application_executor import infer_value, is_resume_upload, supported_site


class ApplicationExecutorTests(unittest.TestCase):
    def test_fills_only_allowlisted_profile_fields(self):
        profile = {"email": "candidate@example.com", "phone": "1234567890"}
        self.assertEqual(infer_value("Email address", profile), ("candidate@example.com", "profile_match"))
        self.assertEqual(infer_value("Phone number", profile), ("1234567890", "profile_match"))

    def test_does_not_answer_sensitive_declarations(self):
        self.assertEqual(
            infer_value("Are you legally authorized to work?", {"work_authorization": "yes"}),
            (None, "sensitive_or_declaration"),
        )

    def test_unknown_question_is_left_for_review(self):
        self.assertEqual(infer_value("Why do you want to work here?", {}), (None, "unrecognized_field"))

    def test_only_explicit_resume_upload_fields_are_eligible(self):
        self.assertTrue(is_resume_upload("Upload your resume (PDF)"))
        self.assertTrue(is_resume_upload("CV / Curriculum Vitae"))
        self.assertFalse(is_resume_upload("Upload cover letter"))
        self.assertFalse(is_resume_upload("Upload transcript"))
        self.assertFalse(is_resume_upload("Attach supporting document"))

    def test_site_detection(self):
        self.assertEqual(supported_site("https://www.linkedin.com/jobs/view/123"), "linkedin")
        self.assertEqual(supported_site("https://boards.greenhouse.io/example/jobs/123"), "career_portal")
        self.assertEqual(supported_site("https://careers.example.org/jobs/123"), "generic_review_only")


if __name__ == "__main__":
    unittest.main()
