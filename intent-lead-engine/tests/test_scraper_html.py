import unittest
from pathlib import Path

from scraper import scrape_html_posts


class TestHTMLScraper(unittest.TestCase):
    """Tests for HTML-based post extraction."""

    def setUp(self):
        self.fixture = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "sample_forum.html"
        )

    def test_extracts_posts_from_html(self):
        """The scraper should extract all valid forum posts."""

        html = self.fixture.read_text(
            encoding="utf-8"
        )

        posts = scrape_html_posts(
            html=html,
            source="local-test",
        )

        self.assertEqual(
            len(posts),
            3,
        )

    def test_extracts_author_and_title(self):
        """Author and title should be extracted correctly."""

        html = self.fixture.read_text(
            encoding="utf-8"
        )

        posts = scrape_html_posts(
            html=html,
            source="local-test",
        )

        self.assertEqual(
            posts[0].author,
            "Jamie",
        )

        self.assertEqual(
            posts[0].title,
            "Thinking about switching POS after another outage",
        )

    def test_extracts_body(self):
        """Post body should be extracted."""

        html = self.fixture.read_text(
            encoding="utf-8"
        )

        posts = scrape_html_posts(
            html=html,
            source="local-test",
        )

        self.assertIn(
            "seriously considering switching systems",
            posts[0].body,
        )


if __name__ == "__main__":
    unittest.main()
