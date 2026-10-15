import csv
import tempfile
import unittest
from pathlib import Path

from application_queue import canonical_url, connect, import_csv, transition


class ApplicationQueueTests(unittest.TestCase):
    def test_canonical_url_removes_tracking_and_www(self):
        self.assertEqual(
            canonical_url("https://www.example.com/jobs/1/?utm_source=x#apply"),
            "https://example.com/jobs/1",
        )

    def test_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "leads.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Company", "Apply Link", "qualification_score"])
                writer.writeheader()
                writer.writerow({"Job Title": "Python Engineer", "Company": "Example", "Apply Link": "https://example.com/jobs/1?utm_source=x", "qualification_score": "40"})
            conn = connect(root / "queue.db")
            try:
                self.assertEqual(import_csv(conn, csv_path), (1, 0))
                self.assertEqual(import_csv(conn, csv_path), (0, 1))
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
            finally:
                conn.close()

    def test_state_transition_is_validated_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "queue.db")
            try:
                conn.execute(
                    "INSERT INTO jobs(canonical_url,title,company,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    ("https://example.com/job", "Engineer", "Example", "DISCOVERED", "now", "now"),
                )
                conn.commit()
                job_id = conn.execute("SELECT id FROM jobs").fetchone()[0]
                transition(conn, job_id, "QUALIFIED", "Passed initial screen")
                self.assertEqual(conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()[0], "QUALIFIED")
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM application_events").fetchone()[0], 1)
                with self.assertRaises(ValueError):
                    transition(conn, job_id, "SUBMITTED", "Invalid direct transition")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
