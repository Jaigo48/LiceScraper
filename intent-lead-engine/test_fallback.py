import unittest
from pathlib import Path

from scraper import scrape_with_fallback


class TestScraperFallback(unittest.TestCase):
    """Tests for resilient web-to-local ingestion."""

    def setUp(self):
        self.dataset = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "sample_posts.json"
        )

    def test_failed_web_request_uses_local_dataset(self):
        """
        If the webpage cannot be reached, the scraper should
        automatically use the bundled JSON dataset.
        """

        posts, method = scrape_with_fallback(
            url="http://127.0.0.1:1/does-not-exist",
            source="fallback-test",
            fallback_path=self.dataset,
            timeout=2,
        )

        self.assertEqual(
            method,
            "fallback",
        )

        self.assertEqual(
            len(posts),
            6,
        )

    def test_fallback_posts_are_valid(self):
        """Fallback records should be normal Post objects."""

        posts, method = scrape_with_fallback(
            url="http://127.0.0.1:1/does-not-exist",
            source="fallback-test",
            fallback_path=self.dataset,
            timeout=2,
        )

        self.assertEqual(
            method,
            "fallback",
        )

        for post in posts:
            self.assertTrue(post.post_id)
            self.assertTrue(post.author)
            self.assertTrue(post.title)


if __name__ == "__main__":
    unittest.main()
