"""ETL orchestrator: fetch from all sources, score, write to Firestore."""

from __future__ import annotations

from datetime import datetime, date

import streamlit as st

from db import write_event_batch
from scoring import score_batch
from scraper import fetch_all_sources


def run_etl(days_back: int = 90) -> dict:
    """
    Full ETL pipeline:
    1. Fetch all sources (HN Algolia + 3 RSS feeds)
    2. Score each event (layoff_certainty + ai_causality)
    3. Write to Firestore with deduplication
    4. Return summary stats

    Returns dict with keys: total_fetched, total_scored, total_written, errors
    """
    stats = {
        "total_fetched": 0,
        "total_scored": 0,
        "total_written": 0,
        "errors": [],
    }

    try:
        # Step 1: Fetch from all sources
        df_fetched = fetch_all_sources(days_back=days_back)
        if df_fetched.empty:
            stats["errors"].append("No stories fetched from any source")
            return stats

        stats["total_fetched"] = len(df_fetched)

        # Convert DataFrame rows back to LayoffStory objects for scoring
        from scraper import LayoffStory

        stories = []
        for _, row in df_fetched.iterrows():
            story = LayoffStory(
                company=row["company"],
                title=row["title"],
                url=row["url"],
                date=row["date"],
                source=row["source"],
                employees=row.get("employees"),
                percent_workforce=row.get("percent_workforce"),
                ai_cause=row.get("ai_cause", "unknown"),
                hn_url=row.get("hn_discussion", ""),
                hn_points=row.get("hn_points", 0) or 0,
            )
            stories.append(story)

        # Step 2: Score all events
        scored_events = score_batch(stories)
        stats["total_scored"] = len(scored_events)

        # Step 3: Prepare for Firestore write
        # Convert datetime strings and date objects to datetime objects for Firestore
        for event in scored_events:
            if isinstance(event["date"], str):
                event["date"] = datetime.fromisoformat(event["date"])
            elif isinstance(event["date"], date) and not isinstance(event["date"], datetime):
                # Convert date to datetime at midnight UTC
                event["date"] = datetime.combine(event["date"], datetime.min.time())

        # Step 4: Write to Firestore with deduplication
        try:
            written = write_event_batch(scored_events)
            stats["total_written"] = written
        except Exception as e:
            stats["errors"].append(f"Firestore write failed: {e}")
            return stats

    except Exception as e:
        import traceback
        stats["errors"].append(f"ETL pipeline failed: {e}\n{traceback.format_exc()}")

    return stats


def run_etl_with_ui(days_back: int = 90) -> None:
    """Run ETL and display results in Streamlit UI."""
    with st.spinner("Running ETL pipeline..."):
        stats = run_etl(days_back=days_back)

    if stats["total_written"] > 0:
        st.success(
            f"✅ ETL Complete: {stats['total_fetched']} fetched → "
            f"{stats['total_scored']} scored → {stats['total_written']} written to Firestore"
        )
    elif stats["total_fetched"] > 0:
        st.warning(
            f"⚠️ No new events written. "
            f"Fetched {stats['total_fetched']}, scored {stats['total_scored']} "
            f"(may be duplicates or all already in DB)"
        )
    else:
        st.warning("No stories fetched from sources")

    if stats["errors"]:
        st.error("Errors during ETL:")
        for err in stats["errors"]:
            st.error(f"  - {err}")
