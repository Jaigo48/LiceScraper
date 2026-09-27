import unittest

import pandas as pd

from finland.importer import (
    add_location_key,
    filter_active_licences,
    load_finland_licences,
)



class TestFinlandImporter(unittest.TestCase):
    """Tests for the Finnish alcohol licence importer."""

    def test_loads_licences(self):
        """The official Finnish licence file should load."""

        df = load_finland_licences()

        self.assertGreater(
            len(df),
            0,
        )

    def test_location_key_ignores_operator(self):
        """The physical location key should not contain operator ID."""

        df = load_finland_licences()
        df = add_location_key(df)

        self.assertIn(
            "location_key",
            df.columns,
        )

        self.assertNotIn(
            df.iloc[0]["operator_id"],
            df.iloc[0]["location_key"],
        )

    def test_location_keys_are_created(self):
        """Every licence record should have a location key."""

        df = load_finland_licences()
        df = add_location_key(df)

        self.assertEqual(
            len(df),
            10240,
        )

        self.assertEqual(
            df["location_key"].nunique(),
            9097,
        )
    def test_filters_inactive_licences(self):
        """Active filtering should exclude future and expired licences."""

        df = load_finland_licences()
        active = filter_active_licences(df)

        today = pd.Timestamp.today().normalize()

        self.assertTrue(
            (active["licence_start_date"] <= today).all()
        )

        self.assertTrue(
            (
                active["licence_end_date"].isna()
                | (active["licence_end_date"] >= today)
            ).all()
        )

    def test_location_key_is_stable(self):
        """The same physical location should produce the same key."""

        df = load_finland_licences()
        df = add_location_key(df)

        first = df.iloc[0]

        self.assertEqual(
            first["location_key"],
            "MERISATAMARANTA 10|00150|HELSINKI",
        )


if __name__ == "__main__":
    unittest.main()

