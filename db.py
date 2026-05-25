"""Firestore connection and utilities for ai-fires project."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentReference

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def _get_credentials():
    """Load Firebase credentials.

    Priority order:
    1. Streamlit secrets as TOML table [firebase] (most reliable on Streamlit Cloud)
    2. Streamlit secrets as JSON string FIREBASE_CREDENTIALS (fallback)
    3. Local file .secrets/ai-fires-sa.json (local development)
    """
    if HAS_STREAMLIT:
        try:
            # Option 1: TOML table [firebase] - returns a dict-like object
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # private_key in TOML often has escaped \n, normalize them
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                return credentials.Certificate(cred_dict)
        except (KeyError, AttributeError, FileNotFoundError):
            pass

        try:
            # Option 2: JSON string FIREBASE_CREDENTIALS (legacy)
            firebase_cred = st.secrets.get("FIREBASE_CREDENTIALS")
            if firebase_cred:
                if isinstance(firebase_cred, str):
                    cred_dict = json.loads(firebase_cred)
                else:
                    cred_dict = dict(firebase_cred)
                return credentials.Certificate(cred_dict)
        except (KeyError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass

    # Option 3: local file
    cred_path = os.path.join(os.path.dirname(__file__), ".secrets", "ai-fires-sa.json")
    if os.path.exists(cred_path):
        return credentials.Certificate(cred_path)

    raise FileNotFoundError(
        "Firebase credentials not found. On Streamlit Cloud, add a [firebase] "
        "table to Secrets. Locally, place ai-fires-sa.json in .secrets/ directory."
    )


if not firebase_admin._apps:
    cred = _get_credentials()
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


# ────────────────────────── Custom RSS sources ──────────────────────────
# Le fonti hardcoded in scraper.py sono sempre attive. Questa collection
# contiene SOLO fonti aggiuntive caricate dall'utente via UI Admin.
# Schema documento: {name, url, enabled, created_at}.

def get_custom_sources(include_disabled: bool = False) -> list[dict]:
    """Restituisce le fonti RSS custom registrate in Firestore."""
    query = db.collection("custom_sources")
    docs = list(query.stream())
    sources = [{"id": d.id, **d.to_dict()} for d in docs]
    if not include_disabled:
        sources = [s for s in sources if s.get("enabled", True)]
    sources.sort(key=lambda s: s.get("name", "").lower())
    return sources


def add_custom_source(name: str, url: str) -> str:
    """Aggiunge una fonte RSS custom. Solleva ValueError se nome già usato.

    Returns: ID del documento creato.
    """
    name = name.strip()
    url = url.strip()
    if not name or not url:
        raise ValueError("name e url sono obbligatori")
    if not url.startswith(("http://", "https://")):
        raise ValueError("url deve iniziare con http:// o https://")

    # Verifica uniqueness sul nome (case-insensitive)
    existing = [s for s in get_custom_sources(include_disabled=True)
                if s.get("name", "").lower() == name.lower()]
    if existing:
        raise ValueError(f"esiste già una fonte chiamata '{name}'")

    doc_ref = db.collection("custom_sources").add({
        "name": name,
        "url": url,
        "enabled": True,
        "created_at": datetime.utcnow(),
    })
    return doc_ref[1].id


def delete_custom_source(source_id: str) -> None:
    """Elimina una fonte custom dato il suo doc ID."""
    db.collection("custom_sources").document(source_id).delete()


def toggle_custom_source(source_id: str, enabled: bool) -> None:
    """Abilita/disabilita una fonte custom senza eliminarla."""
    db.collection("custom_sources").document(source_id).update({"enabled": enabled})
