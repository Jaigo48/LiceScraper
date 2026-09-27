import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


class TestPipeline(unittest.TestCase):
    """End-to-end tests for the command-line application."""

    def setUp(self):
        self.project_root = (
            Path(__file__).resolve().parent.parent
        )

    def test_mock_pipeline_runs(self):
        """The complete mock pipeline should execute successfully."""

        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--mode",
                "mock",
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "Pipeline complete.",
            result.stdout,
        )

    def test_json_output_contains_six_leads(self):
        """The pipeline should produce six JSON records."""

        output_file = (
            self.project_root
            / "output_leads.json"
        )

        with output_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            leads = json.load(file)

        self.assertEqual(
            len(leads),
            6,
        )

    def test_csv_output_contains_six_leads(self):
        """The pipeline should produce six CSV records."""

        output_file = (
            self.project_root
            / "output_leads.csv"
        )

        with output_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(
            len(rows),
            6,
        )


if __name__ == "__main__":
    unittest.main()
