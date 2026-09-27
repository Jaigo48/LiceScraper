import unittest
from pathlib import Path

from scraper import load_sample_posts


class TestScraper(unittest.TestCase):
    """Tests for the sample-post ingestion layer."""

    def setUp(self):
        self.dataset = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "sample_posts.json"
        )

    def test_sample_dataset_loads(self):
        """The bundled dataset should load successfully."""

        posts = load_sample_posts(self.dataset)

        self.assertEqual(len(posts), 6)

    def test_posts_have_required_fields(self):
        """Every post should contain the fields the pipeline needs."""

        posts = load_sample_posts(self.dataset)

        for post in posts:
            self.assertTrue(post.post_id)
            self.assertTrue(post.author)
            self.assertTrue(post.title)
            self.assertTrue(post.body)


if __name__ == "__main__":
    unittest.main()
