"""Firestore connection and utilities for ai-fires project."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentReference

# Init Firebase
_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), ".secrets", "ai-fires-sa.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {"projectId": "ai-fires"})

db = firestore.client()


def write_layoff_event(
    company: str,
    title: str,
    url: str,
    date: datetime,
    source: str,
    employees: Optional[int] = None,
    percent_workforce: Optional[float] = None,
    layoff_certainty: int = 3,  # 1-5
    ai_causality: int = 2,  # 1-5
    hn_url: str = "",
    hn_points: int = 0,
) -> str:
    """Write a single layoff event to Firestore. Returns document ID."""
    doc_ref = db.collection("layoff_events").add({
        "company": company,
        "title": title,
        "url": url,
        "date": date,
        "source": source,
        "employees": employees,
        "percent_workforce": percent_workforce,
        "layoff_certainty": layoff_certainty,
        "ai_causality": ai_causality,
        "hn_url": hn_url,
        "hn_points": hn_points,
        "created_at": datetime.utcnow(),
    })
    return doc_ref[1].id


def get_layoff_events(days_back: int = 90) -> list[dict]:
    """Fetch all layoff events from the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    query = db.collection("layoff_events").where("date", ">=", cutoff).order_by("date", direction=firestore.Query.DESCENDING)
    docs = query.stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def dedup_check(company: str, title_key: str) -> bool:
    """Check if (company, title_key) already exists. Returns True if exists."""
    query = db.collection("layoff_events").where("company", "==", company).where("_title_key", "==", title_key)
    try:
        query.limit(1).stream().__next__()
        return True
    except StopIteration:
        return False


def write_event_batch(events: list[dict]) -> int:
    """Batch write events. Returns count written."""
    batch = db.batch()
    count = 0

    for event in events:
        title_key = event["title"].lower()[:60]
        if not dedup_check(event["company"], title_key):
            ref = db.collection("layoff_events").document()
            batch.set(ref, {**event, "_title_key": title_key, "created_at": datetime.utcnow()})
            count += 1

    batch.commit()
    return count
