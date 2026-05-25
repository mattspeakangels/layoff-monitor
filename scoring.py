"""Dual-scoring logic for layoff events: certainty and AI causality."""

from __future__ import annotations

import re
from scraper import LayoffStory


# --- Source certainty mapping ---
# Rationale: Official/Reuters/Bloomberg have lower retraction rate than HN/Google News
SOURCE_CERTAINTY = {
    "SEC Filing (8-K)": 5,
    "Reuters": 5,
    "Bloomberg": 5,
    "TechCrunch": 3,
    "Hacker News": 2,
    "Google News – AI layoffs": 2,
    "Google News – replaced by AI": 2,
}


def _score_layoff_certainty(source: str, title: str, employees: int | None) -> int:
    """
    Score layoff event certainty (1-5) based on:
    - Source credibility (Reuters/Bloomberg=5, TechCrunch=3, HN/Google=2)
    - Explicit numbers (presence of employee count increases confidence)

    Returns int 1-5.
    """
    base_score = SOURCE_CERTAINTY.get(source, 2)  # Default to 2 (unverified)

    # Boost score if explicit employee count is mentioned
    if employees and employees > 0:
        base_score = min(5, base_score + 1)

    return max(1, min(5, base_score))


def _score_ai_causality(
    title: str,
    url: str,
    ai_cause_level: str,  # "high" / "medium" / "low" from scraper
    source: str,
) -> int:
    """
    Score AI causality (1-5) based on:
    - AI cause level from scraper heuristics ("high"=strong evidence, "medium"=mentioned, "low"=none)
    - Source type (TechCrunch AI analysis > HN > Google News)
    - Explicit causation phrases in title/URL

    Returns int 1-5.
    """
    blob = f"{title} {url}".lower()

    # High AI cause: explicit company statement or Challenger-style analysis
    if ai_cause_level == "high":
        # Detect explicit causation: "refocus on AI", "replaced by AI", "to invest in AI"
        if re.search(
            r"\b(?:refocus(?:ing)?\s+on\s+ai|replaced?\s+by\s+ai|citing\s+ai|"
            r"to\s+(?:invest|spend|hire)\s+(?:more\s+)?(?:in\s+)?ai|"
            r"shift(?:ing)?\s+to\s+(?:capture\s+)?(?:more\s+)?ai)\b",
            blob,
        ):
            return 5

        # Strong inference from TechCrunch or similar
        if "techcrunch" in source.lower():
            return 4
        return 4

    # Medium AI cause: AI explicitly mentioned as factor
    if ai_cause_level == "medium":
        # Boost if from TechCrunch analysis
        if "techcrunch" in source.lower():
            return 3
        return 3

    # Low AI cause: no AI mention or only tangential reference
    # Could still score 1 if context suggests automation/AI displacement
    if re.search(r"\b(?:automation|replace|automat|workforce shift)\b", blob):
        return 1
    return 1


def score_layoff_event(story: LayoffStory) -> dict:
    """
    Score a single LayoffStory on both dimensions.

    Returns enriched dict with layoff_certainty and ai_causality scores added.
    """
    certainty = _score_layoff_certainty(story.source, story.title, story.employees)
    causality = _score_ai_causality(story.title, story.url, story.ai_cause, story.source)

    return {
        **story.to_row(),
        "layoff_certainty": certainty,
        "ai_causality": causality,
    }


def score_batch(stories: list[LayoffStory]) -> list[dict]:
    """Score multiple stories. Returns list of scored event dicts."""
    return [score_layoff_event(s) for s in stories]
