import unittest

from enricher import EnrichmentEngine
from scraper import Post


class TestEnrichmentEngine(unittest.TestCase):
    """Tests for offline lead classification."""

    def setUp(self):
        self.engine = EnrichmentEngine(mode="mock")

    def test_explicit_switching_is_high_intent(self):
        """Explicit POS replacement language should be High."""

        post = Post(
            post_id="test-high",
            source="test",
            author="Test User",
            title="Leaving our current POS",
            body="We have decided to leave our current POS.",
            url="https://example.com/test-high",
        )

        result = self.engine.enrich(post)

        self.assertEqual(result["intent"], "High")
        self.assertGreaterEqual(
            result["confidence"],
            0.80,
        )

    def test_payment_problem_is_not_low(self):
        """A concrete payment problem should produce a meaningful signal."""

        post = Post(
            post_id="test-payment",
            source="test",
            author="Test User",
            title="Processing fees are painful",
            body=(
                "Our credit card processing fees are getting "
                "painful and we are looking at alternatives."
            ),
            url="https://example.com/test-payment",
        )

        result = self.engine.enrich(post)

        self.assertEqual(result["intent"], "Medium")
        self.assertTrue(result["pain_points"])

    def test_general_question_is_low(self):
        """A generic POS question should remain Low."""

        post = Post(
            post_id="test-low",
            source="test",
            author="Test User",
            title="What POS do you use?",
            body="Just curious what POS systems other owners use.",
            url="https://example.com/test-low",
        )

        result = self.engine.enrich(post)

        self.assertEqual(result["intent"], "Low")

    def test_outreach_is_generated(self):
        """Every classified post should receive outreach text."""

        post = Post(
            post_id="test-outreach",
            source="test",
            author="Jamie",
            title="POS outage",
            body="Our POS keeps crashing.",
            url="https://example.com/test-outreach",
        )

        result = self.engine.enrich(post)

        self.assertTrue(result["outreach_email"])
        self.assertIn(
            "Jamie",
            result["outreach_email"],
        )

    def test_confidence_is_valid(self):
        """Confidence must always be between 0 and 1."""

        post = Post(
            post_id="test-confidence",
            source="test",
            author="Jamie",
            title="POS question",
            body="What POS do you use?",
            url="https://example.com/test-confidence",
        )

        result = self.engine.enrich(post)

        self.assertGreaterEqual(
            result["confidence"],
            0.0,
        )

        self.assertLessEqual(
            result["confidence"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
