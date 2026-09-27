#!/usr/bin/env python3

"""
Data ingestion for the Intent-Trigger Lead Engine.

The project is intentionally offline-first:
the bundled JSON dataset provides a reliable demo without requiring
an internet connection or API key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Post:
    """One normalized restaurant-operator discussion."""

    post_id: str
    source: str
    author: str
    title: str
    body: str
    url: str = ""


def load_sample_posts(path: Path) -> list[Post]:
    """Load restaurant posts from the bundled JSON dataset."""

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The sample dataset must contain a JSON list.")

    posts: list[Post] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        posts.append(
            Post(
                post_id=str(item.get("post_id", "")),
                source=str(item.get("source", "sample")),
                author=str(item.get("author", "Unknown")),
                title=str(item.get("title", "")),
                body=str(item.get("body", "")),
                url=str(item.get("url", "")),
            )
        )

    return posts


if __name__ == "__main__":
    dataset = Path(__file__).parent / "data" / "sample_posts.json"
    posts = load_sample_posts(dataset)

    print(f"Loaded {len(posts)} posts.")

    for post in posts:
        print(f"- {post.author}: {post.title}")
