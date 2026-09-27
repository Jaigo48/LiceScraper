#!/usr/bin/env python3

"""
Data ingestion for the Intent-Trigger Lead Engine.

The project is intentionally offline-first.

Supported ingestion methods:

1. Bundled JSON dataset
   - Always available.
   - Requires no internet.
   - Used as the fallback/demo dataset.

2. Generic HTML scraper
   - Uses requests + BeautifulSoup.
   - Extracts posts using configurable CSS selectors.
   - Intended for permitted public webpages.

The scraper never assumes that a remote website will be available.
Callers can catch network/parsing errors and fall back to the
bundled dataset.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Post:
    """One normalized restaurant-operator discussion."""

    post_id: str
    source: str
    author: str
    title: str
    body: str
    url: str = ""
    street_address: str = ""
    postal_code: str = ""
    municipality: str = ""


def load_sample_posts(path: Path) -> list[Post]:
    """Load restaurant posts from the bundled JSON dataset."""

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "The sample dataset must contain a JSON list."
        )

    posts: list[Post] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        posts.append(
            Post(
                post_id=str(
                    item.get("post_id", "")
                ),
                source=str(
                    item.get("source", "sample")
                ),
                author=str(
                    item.get("author", "Unknown")
                ),
                title=str(
                    item.get("title", "")
                ),
                body=str(
                    item.get("body", "")
                ),
                url=str(
                    item.get("url", "")
                ),
		street_address=str(
		    item.get("street_address", "")
		),
		postal_code=str(
		    item.get("postal_code", "")
		),
		municipality=str(
		    item.get("municipality", "")
		),

            )
        )

    return posts


def fetch_html(
    url: str,
    timeout: int = 15,
) -> str:
    """
    Download HTML from a public webpage.

    This function deliberately has a short timeout so that a
    failed remote source does not make the whole pipeline hang.
    """

    headers = {
        "User-Agent": (
            "IntentTriggerLeadEngine/1.0 "
            "(portfolio research tool)"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.text


def scrape_html_posts(
    html: str,
    source: str,
    base_url: str = "",
    post_selector: str = ".post",
    title_selector: str = ".post-title",
    author_selector: str = ".post-author",
    body_selector: str = ".post-body",
) -> list[Post]:
    """
    Extract normalized Post objects from HTML.

    CSS selectors are configurable because every website has a
    different HTML structure.

    Example HTML:

        <article class="post">
            <h2 class="post-title">POS problem</h2>
            <span class="post-author">Jamie</span>
            <div class="post-body">Our POS keeps crashing.</div>
        </article>
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    elements = soup.select(post_selector)

    posts: list[Post] = []

    for index, element in enumerate(elements, start=1):

        title_element = element.select_one(
            title_selector
        )

        author_element = element.select_one(
            author_selector
        )

        body_element = element.select_one(
            body_selector
        )

        title = (
            title_element.get_text(
                " ",
                strip=True,
            )
            if title_element
            else ""
        )

        author = (
            author_element.get_text(
                " ",
                strip=True,
            )
            if author_element
            else "Unknown"
        )

        body = (
            body_element.get_text(
                " ",
                strip=True,
            )
            if body_element
            else ""
        )

        # Skip incomplete records rather than creating
        # unusable leads.
        if not title and not body:
            continue

        posts.append(
            Post(
                post_id=f"{source}-{index:03d}",
                source=source,
                author=author,
                title=title,
                body=body,
                url=base_url,
            )
        )

    return posts


def scrape_public_page(
    url: str,
    source: str,
    timeout: int = 15,
    post_selector: str = ".post",
    title_selector: str = ".post-title",
    author_selector: str = ".post-author",
    body_selector: str = ".post-body",
) -> list[Post]:
    """
    Fetch and parse a public HTML page.

    Network errors and HTTP errors are allowed to propagate to
    the caller so the main pipeline can decide whether to fall
    back to local data.
    """

    html = fetch_html(
        url=url,
        timeout=timeout,
    )

    return scrape_html_posts(
        html=html,
        source=source,
        base_url=url,
        post_selector=post_selector,
        title_selector=title_selector,
        author_selector=author_selector,
        body_selector=body_selector,
    )


if __name__ == "__main__":
    dataset = (
        Path(__file__).parent
        / "data"
        / "sample_posts.json"
    )

    posts = load_sample_posts(dataset)

    print(f"Loaded {len(posts)} posts.")

    for post in posts:
        print(
            f"- {post.author}: {post.title}"
        )


def scrape_with_fallback(
    url: str,
    source: str,
    fallback_path: Path,
    timeout: int = 15,
) -> tuple[list[Post], str]:
    """
    Try to scrape a public webpage and fall back to the bundled
    dataset if the request or parsing fails.

    Returns:
        A tuple containing:
            - the list of posts
            - the ingestion method used
    """

    try:
        posts = scrape_public_page(
            url=url,
            source=source,
            timeout=timeout,
        )

        if posts:
            return posts, "web"

        print(
            "Web page returned no posts; "
            "using local fallback dataset."
        )

    except (
        requests.RequestException,
        ValueError,
        RuntimeError,
    ) as exc:
        print(
            f"Web ingestion failed: {exc}"
        )

    print(
        "Using bundled sample dataset."
    )

    return (
        load_sample_posts(fallback_path),
        "fallback",
    )
