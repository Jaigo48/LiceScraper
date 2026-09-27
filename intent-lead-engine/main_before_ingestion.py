#!/usr/bin/env python3

"""
Intent-Trigger Lead Engine.

Examples:

    python3 main.py --mode mock
    python3 main.py --mode live

Mock mode:
    Completely offline and requires no API key.

Live mode:
    Uses the configured Gemini API key.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from enricher import EnrichmentEngine
from scraper import load_sample_posts


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sample_posts.json"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Restaurant POS Intent-Trigger Lead Engine"
    )

    parser.add_argument(
        "--mode",
        choices=["mock", "live"],
        default="mock",
        help="Choose offline mock mode or live Gemini mode.",
    )

    return parser.parse_args()


def save_json(leads: list[dict[str, Any]]) -> Path:
    """Save leads to JSON."""

    output_file = BASE_DIR / "output_leads.json"

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            leads,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_file


def save_csv(leads: list[dict[str, Any]]) -> Path:
    """Save leads to CSV."""

    output_file = BASE_DIR / "output_leads.csv"

    fieldnames = [
        "post_id",
        "source",
        "author",
        "title",
        "url",
        "intent",
        "confidence",
        "pain_points",
        "outreach_email",
        "enrichment_mode",
    ]

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for lead in leads:

            row = lead.copy()

            row["pain_points"] = "; ".join(
                row["pain_points"]
            )

            writer.writerow(row)

    return output_file


def run_pipeline(mode: str) -> list[dict[str, Any]]:
    """Load posts and enrich every post."""

    posts = load_sample_posts(DATA_FILE)

    print(f"Posts loaded    : {len(posts)}")
    print(f"Engine mode     : {mode}")

    engine = EnrichmentEngine(mode=mode)

    leads: list[dict[str, Any]] = []

    for post in posts:

        try:
            result = engine.enrich(post)

        except Exception as exc:
            print()
            print(
                f"Warning: Could not enrich "
                f"{post.post_id}: {exc}"
            )

            continue

        lead = {
            "post_id": post.post_id,
            "source": post.source,
            "author": post.author,
            "title": post.title,
            "url": post.url,
            **result,
        }

        leads.append(lead)

    return leads


def print_summary(leads: list[dict[str, Any]]) -> None:
    """Print a human-readable summary."""

    high = sum(
        1
        for lead in leads
        if lead["intent"] == "High"
    )

    medium = sum(
        1
        for lead in leads
        if lead["intent"] == "Medium"
    )

    low = sum(
        1
        for lead in leads
        if lead["intent"] == "Low"
    )

    print()
    print("Lead summary")
    print("------------")
    print(f"High intent    : {high}")
    print(f"Medium intent  : {medium}")
    print(f"Low intent     : {low}")


def main() -> None:
    """Application entry point."""

    args = parse_args()

    print()
    print("Intent-Trigger Lead Engine")
    print("============================")

    # Give the user an immediate explanation if live mode
    # was requested without a configured API key.
    if args.mode == "live":
        if not os.getenv("GEMINI_API_KEY", "").strip():
            print()
            print("Live mode requires GEMINI_API_KEY.")
            print()
            print(
                "No API key is configured, so the program "
                "cannot contact Gemini."
            )
            print()
            print(
                "For the free offline demo, run:"
            )
            print()
            print(
                "    python3 main.py --mode mock"
            )
            print()

            return

    try:
        leads = run_pipeline(args.mode)

    except FileNotFoundError as exc:
        print()
        print(f"Error: {exc}")
        return

    except Exception as exc:
        print()
        print(f"Pipeline error: {exc}")
        return

    if not leads:
        print()
        print("No leads were produced.")
        return

    json_file = save_json(leads)
    csv_file = save_csv(leads)

    print()
    print(f"CSV output      : {csv_file}")
    print(f"JSON output     : {json_file}")

    print_summary(leads)

    print()
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
