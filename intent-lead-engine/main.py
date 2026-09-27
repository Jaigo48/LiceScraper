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

import pandas as pd
from enricher import EnrichmentEngine
from finland.importer import load_finland_licences
from finland.lead_matcher import attach_finland_licence
from scraper import Post, load_sample_posts, scrape_with_fallback


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sample_posts.json"


def load_custom_posts(file_path: Path) -> list[Post]:
    """Load posts from a JSON, CSV, or Excel file."""
    ext = file_path.suffix.lower()

    if ext == ".json":
        return load_sample_posts(file_path)

    elif ext in {".csv", ".xlsx"}:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        posts = []
        for index, row in df.iterrows():
            posts.append(
                Post(
                    post_id=str(row.get("post_id", f"custom-{index}")),
                    source=str(row.get("source", "custom_file")),
                    author=str(row.get("author", "unknown")),
                    title=str(row.get("title", "")),
                    body=str(row.get("body", "")),
                    url=str(row.get("url", "")),
                    street_address=str(row.get("street_address", "")) if pd.notna(row.get("street_address")) else None,
                    postal_code=str(row.get("postal_code", "")) if pd.notna(row.get("postal_code")) else None,
                    municipality=str(row.get("municipality", "")) if pd.notna(row.get("municipality")) else None,
                )
            )
        return posts
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .json, .csv, or .xlsx")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Restaurant POS Intent-Trigger Lead Engine"
    )

    parser.add_argument(
        "--mode",
        choices=["mock", "web", "live"],
        default="mock",
        help="mock=offline, web=web+fallback, live=web+fallback+Gemini.",
    )

    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a custom JSON, CSV, or XLSX post file.",
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
            ensure_ascii=False,
            indent=2,
            default=str,
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
        "ingestion_mode",
        "street_address",
        "postal_code",
        "municipality",
        "finland_licence_match",
        "finland_licence_count",
        "finland_licences",
        "finland_signal_type",
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

            row["finland_licences"] = json.dumps(
                row["finland_licences"],
                ensure_ascii=False,
                default=str,
            )

            writer.writerow(row)

    return output_file


def run_pipeline(mode: str, custom_file: str | None = None) -> list[dict[str, Any]]:
    """Load posts, enrich them, and return structured leads."""

    target_file = Path(custom_file) if custom_file else DATA_FILE

    if mode == "mock":
        posts = load_custom_posts(target_file)
        ingestion_mode = "local"

    else:
        web_url = "https://example.com"

        try:
            posts, ingestion_mode = scrape_with_fallback(
                url=web_url,
                source="public_web",
                fallback_path=target_file,
                timeout=5,
            )

        except Exception as exc:
            print(f"Unexpected ingestion error: {exc}")
            posts = load_custom_posts(target_file)
            ingestion_mode = "fallback"

    # (the rest of run_pipeline stays exactly the same...)
    print(f"Posts loaded    : {len(posts)}")
    print(f"Ingestion mode  : {ingestion_mode}")
    print(f"Engine mode     : {mode}")
    
    finland_df = load_finland_licences()
    print(f"Finnish licences: {len(finland_df)}")

    enrichment_mode = (
        "mock"
        if mode in {"mock", "web"}
        else "live"
    )

    engine = EnrichmentEngine(
        mode=enrichment_mode
    )

    leads: list[dict[str, Any]] = []

    for post in posts:
        try:
            result = engine.enrich(post)

            result["street_address"] = post.street_address
            result["postal_code"] = post.postal_code
            result["municipality"] = post.municipality

            result = attach_finland_licence(
                result,
                finland_df,
            )

            lead = {
                "post_id": post.post_id,
                "source": post.source,
                "author": post.author,
                "title": post.title,
                "url": post.url,
                "ingestion_mode": ingestion_mode,
                **result,
            }

            leads.append(lead)

        except Exception as exc:
            print()
            print(
                f"Warning: Could not enrich "
                f"{getattr(post, 'title', 'post')}: {exc}"
            )

            continue

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
        leads = run_pipeline(args.mode, args.file)

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
