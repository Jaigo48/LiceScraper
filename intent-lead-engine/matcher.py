#!/usr/bin/env python3

"""
Conservative matching between restaurant information and
Finnish alcohol licence locations.
"""

from __future__ import annotations

from typing import Optional

from finland.importer import add_location_key, filter_active_licences

import pandas as pd


def match_location(
    df: pd.DataFrame,
    street_address: Optional[str] = None,
    postal_code: Optional[str] = None,
    municipality: Optional[str] = None,
) -> pd.DataFrame:
    """Return licence records matching a supplied physical location."""

    if not street_address or not postal_code or not municipality:
        return df.iloc[0:0].copy()

    street = str(street_address).strip().upper()
    postal = str(postal_code).strip().upper()
    city = str(municipality).strip().upper()

    street_values = (
        df["street_address"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    postal_values = (
        df["postal_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    city_values = (
        df["municipality"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    matches = (
        (street_values == street)
        & (postal_values == postal)
        & (city_values == city)
    )

    return df.loc[matches].copy()


def match_active_location(
    df: pd.DataFrame,
    street_address: Optional[str] = None,
    postal_code: Optional[str] = None,
    municipality: Optional[str] = None,
) -> pd.DataFrame:
    """Match only currently active licences at a physical location."""

    active_df = filter_active_licences(df)
    active_df = add_location_key(active_df)

    return match_location(
        active_df,
        street_address=street_address,
        postal_code=postal_code,
        municipality=municipality,
    )

