#!/usr/bin/env python3

"""
Restaurant POS lead enrichment engine.

Supports two modes:

    mock
        Completely offline. No API key required.

    live
        Uses the Gemini REST API. Requires GEMINI_API_KEY.

The mock engine is intentionally retained as a fallback so the
portfolio project can always be demonstrated without paid services.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from scraper import Post


class EnrichmentEngine:
    """Analyze restaurant discussions for POS buying intent."""

    SWITCHING_SIGNALS = [
        "switching pos",
        "switch pos",
        "switch from",
        "replace our pos",
        "replacement system",
        "replacement pos",
        "new pos",
        "leaving our current pos",
        "change our pos",
        "other pos systems",
        "decided to leave",
        "looking at other pos",
    ]

    RESEARCH_SIGNALS = [
        "researching alternatives",
        "researching options",
        "comparing",
        "looking for",
        "looking at",
        "evaluating",
        "alternatives",
        "recommendations",
        "pricing",
        "payment alternatives",
    ]

    PAIN_PATTERNS = {
        "payment_cost": [
            "processing fees",
            "credit card processing",
            "payment processing",
            "transaction fees",
            "payment costs",
        ],
        "hardware": [
            "slow pos",
            "slow terminal",
            "slow hardware",
            "pos hardware",
            "faster hardware",
        ],
        "reliability": [
            "keeps freezing",
            "pos down",
            "crashes",
            "crashing",
            "outage",
            "freezing",
            "downtime",
        ],
        "support": [
            "customer support",
            "support hasn't",
            "support has not",
            "poor support",
            "support isn't",
            "support is not",
        ],
        "reporting": [
            "limited reporting",
            "reporting",
            "analytics",
            "reports",
        ],
    }

    FRIENDLY_PAIN_NAMES = {
        "payment_cost": "High payment or credit-card processing costs",
        "hardware": "Slow or unreliable POS hardware",
        "reliability": "POS crashes, freezing, or downtime",
        "support": "Poor or slow POS customer support",
        "reporting": "Limited or unreliable reporting",
    }

    def __init__(self, mode: str = "mock") -> None:
        """Create an enrichment engine."""

        if mode not in {"mock", "live"}:
            raise ValueError(
                "Mode must be either 'mock' or 'live'."
            )

        self.mode = mode
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()

    def enrich(self, post: Post) -> dict[str, Any]:
        """Enrich a post using the selected engine."""

        if self.mode == "live":
            return self._enrich_live(post)

        return self._enrich_mock(post)

    # =========================================================
    # MOCK ENGINE
    # =========================================================

    def _enrich_mock(self, post: Post) -> dict[str, Any]:
        """Perform deterministic offline analysis."""

        text = f"{post.title}\n{post.body}".lower()

        switching_score = self._count_matches(
            text,
            self.SWITCHING_SIGNALS,
        )

        research_score = self._count_matches(
            text,
            self.RESEARCH_SIGNALS,
        )

        pain_points = self._detect_pain_points(text)

        if switching_score > 0:
            intent = "High"
            confidence = min(
                0.95,
                0.82 + (len(pain_points) * 0.04),
            )

        elif research_score > 0 and pain_points:
            intent = "Medium"
            confidence = min(
                0.88,
                0.68 + (len(pain_points) * 0.05),
            )

        elif len(pain_points) >= 2:
            intent = "Medium"
            confidence = 0.72

        elif len(pain_points) == 1:
            intent = "Medium"
            confidence = 0.65

        else:
            intent = "Low"
            confidence = 0.55

        if not pain_points:
            pain_points = [
                "No specific POS pain point detected"
            ]

        outreach = self._create_outreach(
            post,
            intent,
            pain_points,
        )

        return {
            "intent": intent,
            "confidence": round(confidence, 2),
            "pain_points": pain_points,
            "outreach_email": outreach,
            "enrichment_mode": "mock",
        }

    # =========================================================
    # LIVE GEMINI ENGINE
    # =========================================================

    def _enrich_live(self, post: Post) -> dict[str, Any]:
        """Analyze a post using the Gemini REST API."""

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Use --mode mock for offline operation, "
                "or configure GEMINI_API_KEY."
            )

        prompt = self._build_prompt(post)

        # Gemini REST endpoint.
        #
        # Keeping this as a direct HTTP request avoids requiring
        # an additional Google SDK on the older Mac.
        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-2.0-flash:generateContent"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = requests.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=30,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Gemini API request failed: {exc}"
            ) from exc

        try:
            data = response.json()

            text = (
                data["candidates"][0]["content"]["parts"][0]["text"]
            )

            result = json.loads(text)

        except (
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                "Gemini returned an unexpected response."
            ) from exc

        return self._validate_live_result(result)

    @staticmethod
    def _build_prompt(post: Post) -> str:
        """Build a constrained JSON classification prompt."""

        return f"""
You are analyzing a public restaurant-operator discussion
for a software sales research portfolio project.

Determine whether the author shows intent to change, replace,
or seriously evaluate a restaurant POS system.

Post title:
{post.title}

Post body:
{post.body}

Return ONLY valid JSON with this exact structure:

{{
  "intent": "High|Medium|Low",
  "confidence": 0.0,
  "pain_points": [
    "short pain point"
  ],
  "outreach_email": "exactly three sentences"
}}

Rules:

- High means the author explicitly indicates they are switching,
  replacing, leaving, or actively choosing another POS.
- Medium means there is a meaningful operational/payment problem
  and/or active research, but replacement intent is not explicit.
- Low means general discussion, curiosity, or weak buying signal.
- Confidence must be between 0.0 and 1.0.
- Do not invent facts about the restaurant.
- Pain points must be supported by the post.
- The outreach must be professional and specific to the post.
- Do not claim that the author requested contact.
- Do not mention this classification system.
"""

    @staticmethod
    def _validate_live_result(
        result: Any,
    ) -> dict[str, Any]:
        """Validate and normalize AI-generated JSON."""

        if not isinstance(result, dict):
            raise RuntimeError(
                "AI result was not a JSON object."
            )

        intent = result.get("intent")
        confidence = result.get("confidence")
        pain_points = result.get("pain_points")
        outreach = result.get("outreach_email")

        if intent not in {"High", "Medium", "Low"}:
            raise RuntimeError(
                "AI returned an invalid intent value."
            )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "AI returned an invalid confidence value."
            ) from exc

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        if not isinstance(pain_points, list):
            raise RuntimeError(
                "AI returned invalid pain points."
            )

        pain_points = [
            str(item).strip()
            for item in pain_points
            if str(item).strip()
        ]

        if not pain_points:
            pain_points = [
                "No specific POS pain point detected"
            ]

        if not isinstance(outreach, str):
            raise RuntimeError(
                "AI returned invalid outreach text."
            )

        return {
            "intent": intent,
            "confidence": round(confidence, 2),
            "pain_points": pain_points,
            "outreach_email": outreach.strip(),
            "enrichment_mode": "gemini",
        }

    # =========================================================
    # SHARED HELPERS
    # =========================================================

    @staticmethod
    def _count_matches(
        text: str,
        phrases: list[str],
    ) -> int:
        """Count signal phrases found in text."""

        return sum(
            1
            for phrase in phrases
            if phrase in text
        )

    def _detect_pain_points(
        self,
        text: str,
    ) -> list[str]:
        """Detect operational pain points."""

        detected: list[str] = []

        for category, phrases in self.PAIN_PATTERNS.items():

            if any(
                phrase in text
                for phrase in phrases
            ):
                detected.append(
                    self.FRIENDLY_PAIN_NAMES[category]
                )

        if any(
            phrase in text
            for phrase in self.SWITCHING_SIGNALS
        ):
            detected.insert(
                0,
                "Considering a POS change or replacement",
            )

        return detected

    @staticmethod
    def _create_outreach(
        post: Post,
        intent: str,
        pain_points: list[str],
    ) -> str:
        """Create a three-sentence mock outreach message."""

        primary = pain_points[0].lower()

        if intent == "High":
            opening = (
                f"Hi {post.author}, I saw your post about "
                f"{primary}."
            )
        else:
            opening = (
                f"Hi {post.author}, I came across your post "
                f"about {primary}."
            )

        if "processing" in primary or "payment" in primary:
            middle = (
                "We work with restaurant operators looking to "
                "reduce payment and POS costs without adding "
                "unnecessary complexity."
            )

        elif "hardware" in primary:
            middle = (
                "We work with restaurant operators looking to "
                "make service faster and reduce POS friction "
                "during busy periods."
            )

        elif "reporting" in primary:
            middle = (
                "We work with restaurant operators looking for "
                "simpler POS workflows and more useful reporting."
            )

        elif "support" in primary:
            middle = (
                "We work with restaurant operators looking for "
                "more reliable POS systems and responsive support."
            )

        else:
            middle = (
                "We work with restaurant operators looking to "
                "reduce POS friction and improve day-to-day "
                "operations."
            )

        third = (
            "If you're still evaluating options, would you be "
            "open to a quick conversation about what you're "
            "looking to improve?"
        )

        return f"{opening} {middle} {third}"


if __name__ == "__main__":
    from pathlib import Path

    from scraper import load_sample_posts

    dataset = (
        Path(__file__).parent
        / "data"
        / "sample_posts.json"
    )

    posts = load_sample_posts(dataset)

    engine = EnrichmentEngine(mode="mock")

    for post in posts:
        result = engine.enrich(post)

        print()
        print("=" * 60)
        print(post.title)
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']}")

        print("Pain points:")

        for pain in result["pain_points"]:
            print(f"  - {pain}")

        print("Outreach:")
        print(result["outreach_email"])
