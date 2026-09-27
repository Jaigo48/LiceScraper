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

   


if __name__ == "__main__":
    unittest.main()
