#!/usr/bin/env python3
from __future__ import annotations

"""
Attach Finnish alcohol licence information to lead records.

Matching is intentionally conservative:
a lead must provide street address, postal code, and municipality.
"""

from typing import Any
import pandas as pd
from finland.importer import detect_new_locations, add_location_key
from finland.matcher import match_active_location

def attach_finland_licence(
    lead: dict[str, Any],
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Return a lead enriched with active Finnish licence match and new-location signals."""

    enriched = lead.copy()

    matches = match_active_location(
        df,
        street_address=lead.get("street_address"),
        postal_code=lead.get("postal_code"),
        municipality=lead.get("municipality"),
    )

    if matches.empty:
        enriched["finland_licence_match"] = False
        enriched["finland_licence_count"] = 0
        enriched["finland_licences"] = []
        enriched["finland_signal_type"] = None
        return enriched

    # Ensure location keys exist on the dataframe for new-location detection
    if "location_key" not in df.columns:
        df = add_location_key(df)

    new_locs_df = detect_new_locations(df)
    new_locs_map = dict(zip(new_locs_df["location_key"], new_locs_df["signal_type"]))

    licences = []
    lead_signal_type = None

    for _, row in matches.iterrows():
        loc_key = row.get("location_key")
        sig_type = new_locs_map.get(loc_key)
        
        if sig_type and not lead_signal_type:
            lead_signal_type = str(sig_type)

        licences.append(
            {
                "licence_number": row["licence_number"],
                "location_name": row["location_name"],
                "operator_name": row["operator_name"],
                "street_address": row["street_address"],
                "postal_code": row["postal_code"],
                "municipality": row["municipality"],
                "licence_start_date": row["licence_start_date"],
                "licence_end_date": row["licence_end_date"],
                "signal_type": str(sig_type) if sig_type else "EXISTING_LOCATION",
            }
        )

    enriched["finland_licence_match"] = True
    enriched["finland_licence_count"] = len(licences)
    enriched["finland_licences"] = licences
    enriched["finland_signal_type"] = lead_signal_type or "EXISTING_LOCATION"

    return enriched
