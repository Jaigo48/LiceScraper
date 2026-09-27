import unittest

from finland.importer import load_finland_licences
from finland.matcher import match_location


class TestFinlandMatcher(unittest.TestCase):
    """Tests for conservative Finnish location matching."""

    def test_exact_location_matches(self):
        """A complete exact location should produce a match."""

        df = load_finland_licences()
        first = df.iloc[0]

        matches = match_location(
            df,
            street_address=first["street_address"],
            postal_code=first["postal_code"],
            municipality=first["municipality"],
        )

        self.assertEqual(
            len(matches),
            1,
        )

    def test_incomplete_location_does_not_match(self):
        """Missing location information should produce no match."""

        df = load_finland_licences()

        matches = match_location(
            df,
            street_address="MERISATAMARANTA 10",
            postal_code="150",
        )

        self.assertEqual(
            len(matches),
            0,
        )

    def test_multiple_licences_at_one_location(self):
        """A location may legitimately have multiple licence records."""

        df = load_finland_licences()

        matches = match_location(
            df,
            street_address="Leppävaarankatu 3-9",
            postal_code="02600",
            municipality="Espoo",
        )

        self.assertEqual(
            len(matches),
            14,
        )


if __name__ == "__main__":
    unittest.main()

