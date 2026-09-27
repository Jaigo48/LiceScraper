import unittest

from finland.importer import load_finland_licences
from finland.lead_matcher import attach_finland_licence


class TestLeadMatcher(unittest.TestCase):
    """Tests for attaching Finnish licence data to leads."""

    def test_exact_location_attaches_licence(self):
        """A lead with an exact location should receive licence data."""

        df = load_finland_licences()
        first = df.iloc[0]

        lead = {
            "post_id": "test-001",
            "street_address": first["street_address"],
            "postal_code": first["postal_code"],
            "municipality": first["municipality"],
        }

        result = attach_finland_licence(
            lead,
            df,
        )

        self.assertTrue(
            result["finland_licence_match"]
        )

        self.assertEqual(
            result["finland_licence_count"],
            1,
        )

        self.assertEqual(
            result["finland_licences"][0]["licence_number"],
            first["licence_number"],
        )

    def test_unknown_location_does_not_attach_licence(self):
        """An unknown location should produce no licence match."""

        df = load_finland_licences()

        lead = {
            "post_id": "test-002",
            "street_address": "UNKNOWN STREET 999",
            "postal_code": "00000",
            "municipality": "UNKNOWN",
        }

        result = attach_finland_licence(
            lead,
            df,
        )

        self.assertFalse(
            result["finland_licence_match"]
        )

        self.assertEqual(
            result["finland_licence_count"],
            0,
        )

        self.assertEqual(
            result["finland_licences"],
            [],
        )


if __name__ == "__main__":
    unittest.main()

