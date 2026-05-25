"""Layoff data scraper — multi-source: HN Algolia, TechCrunch RSS, Google News RSS."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, date
from email.utils import parsedate_to_datetime
from typing import Optional

import pandas as pd
import requests
import streamlit as st

USER_AGENT = "layoff-monitor/1.0 (research)"

# --- Sources ---
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_QUERIES = ["layoffs", "layoff", "cuts jobs", "lays off"]

RSS_SOURCES = {
    "TechCrunch": "https://techcrunch.com/tag/layoffs/feed/",
    "Google News – AI layoffs": "https://news.google.com/rss/search?q=AI+layoffs&hl=en&gl=US&ceid=US:en",
    "Google News – replaced by AI": "https://news.google.com/rss/search?q=%22replaced+by+AI%22+OR+%22job+cuts+artificial+intelligence%22&hl=en&gl=US&ceid=US:en",
}

# --- AI keyword matching ---
AI_KEYWORDS = [
    "ai", "a.i.", "artificial intelligence", "machine learning", "ml",
    "llm", "gpt", "generative", "openai", "anthropic", "deepmind",
    "neural", "deep learning", "data science", "automation", "robotics",
    "autonomous", "chatbot", "copilot",
]

# Phrases that strongly imply AI *caused* the layoff
AI_CAUSE_HIGH = re.compile(
    r"\b(?:refocus(?:ing)?\s+on\s+ai|replaced?\s+by\s+ai|citing\s+ai|"
    r"to\s+(?:invest|spend|hire)\s+(?:more\s+)?(?:in\s+)?ai|"
    r"ai\s+(?:transition|pivot|restructur|capabilit|strateg|investment|hiring)|"
    r"shift(?:ing)?\s+to\s+(?:capture\s+)?(?:more\s+)?ai|"
    r"(?:invest|bet|focus|double.?down)\s+(?:more\s+)?(?:on\s+)?ai|"
    r"in\s+favor\s+of\s+ai|for\s+ai\s+(?:talent|roles|workers)|"
    r"a\.i\.\s+(?:casualties|driven|powered))\b",
    re.I,
)

# --- Parsing helpers ---
EMPLOYEE_PATTERNS_K = [
    re.compile(r"(\d+(?:\.\d+)?)\s*k\s+(?:employees|workers|staff|jobs|people|roles)", re.I),
    re.compile(r"(?:cuts?|lays?\s+off|fires?)\s+(?:over\s+|about\s+|nearly\s+)?(\d+(?:\.\d+)?)\s*k\b", re.I),
]
EMPLOYEE_PATTERNS = [
    re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\b(?!\s*%)\s*(?:employees|workers|staff|jobs|people|roles)", re.I),
    re.compile(r"cuts?\s+(?:over\s+|about\s+|nearly\s+)?(\d{1,3}(?:,\d{3})+|\d+)\b(?!\s*%)", re.I),
    re.compile(r"lays?\s+off\s+(?:over\s+|about\s+|nearly\s+)?(\d{1,3}(?:,\d{3})+|\d+)\b(?!\s*%)", re.I),
    re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\s*(?:layoffs)", re.I),
]
PERCENT_PATTERN = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:its\s+)?(?:staff|workforce|employees|workers)", re.I)
META_ARTICLE_PATTERNS = re.compile(
    r"\b(tracker|receipts?|chronicle|history of|story of|essay|opinion|analysis|"
    r"why\s+(?:tech|the)|the\s+morale|the\s+ai\s+layoff|read\s+\w+'?s?\s+layoff\s+email|"
    r"job\s+market|resume\s+tips?|how\s+to\s+survive)\b",
    re.I,
)
GENERIC_COMPANY = re.compile(
    r"^(another|the|read|tech|big tech|silicon valley|a|an|if|when|how|why|what|is|are)(\s|$)",
    re.I,
)
LAYOFF_TRIGGER = re.compile(
    r"\b(layoff|lay\s+off|cuts?\s+jobs?|fires?\s+\d|lays?\s+off|job\s+cuts?|"
    r"to\s+lay\s+off|laying\s+off|cutting\s+(?:jobs|staff|workers|employees)|"
    r"slashes?\s+(?:jobs|staff|workforce))\b",
    re.I,
)


@dataclass
class LayoffStory:
    company: str
    title: str
    url: str
    date: datetime
    source: str
    employees: Optional[int] = None
    percent_workforce: Optional[float] = None
    ai_cause: str = "unknown"  # high / medium / low / unknown
    hn_url: str = ""
    hn_points: int = 0

    def to_row(self) -> dict:
        # Ensure date is a datetime.datetime for Firestore
        if isinstance(self.date, datetime):
            dt = self.date
        elif isinstance(self.date, date):
            dt = datetime.combine(self.date, datetime.min.time())
        else:
            dt = self.date

        return {
            "source": self.source,
            "date": dt,
            "company": self.company,
            "employees": self.employees,
            "percent_workforce": self.percent_workforce,
            "ai_cause": self.ai_cause,
            "title": self.title,
            "url": self.url,
            "hn_discussion": self.hn_url or None,
            "hn_points": self.hn_points or None,
        }


# --- Extraction helpers ---

def _clean_company(name: str) -> str:
    name = name.strip().rstrip(",.;:")
    name = re.sub(r"'s$", "", name)
    return name.strip()


def _extract_company(title: str) -> str:
    t = re.sub(r"\s+", " ", title).strip()
    m = re.match(
        r"^([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,3}?)"
        r"\s+(?i:(?:is\s+|to\s+|will\s+|set\s+to\s+)?(?:lay(?:s|ing)?\s+off|cuts?|fires?|cutting|fired|axes|slashes))\b",
        t,
    )
    if m:
        return _clean_company(m.group(1))
    m = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,2})", t)
    if m:
        return _clean_company(m.group(1))
    m = re.search(
        r"(?i:layoffs?\s+(?:hitting\s+|at\s+))([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,2})", t
    )
    if m:
        return _clean_company(m.group(1))
    return "Unknown"


def _extract_employees(title: str) -> Optional[int]:
    for pat in EMPLOYEE_PATTERNS_K:
        m = pat.search(title)
        if m:
            try:
                return int(float(m.group(1)) * 1000)
            except ValueError:
                continue
    for pat in EMPLOYEE_PATTERNS:
        m = pat.search(title)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _extract_percent(title: str) -> Optional[float]:
    m = PERCENT_PATTERN.search(title)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def _ai_cause_level(title: str, url: str) -> str:
    blob = f"{title} {url}"
    if AI_CAUSE_HIGH.search(blob):
        return "high"
    blob_lower = blob.lower()
    if any(re.search(rf"\b{re.escape(kw)}\b", blob_lower) for kw in AI_KEYWORDS):
        return "medium"
    return "low"


def _is_ai_related(title: str, url: str) -> bool:
    blob = f"{title} {url}".lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", blob) for kw in AI_KEYWORDS)


def _is_valid_story(title: str, company: str) -> bool:
    if not LAYOFF_TRIGGER.search(title):
        return False
    if META_ARTICLE_PATTERNS.search(title):
        return False
    if GENERIC_COMPANY.match(company) or company == "Unknown":
        return False
    return True


# --- Fetchers ---

def _fetch_hn(days_back: int, max_per_query: int) -> list[LayoffStory]:
    cutoff_ts = int((datetime.now(tz=timezone.utc) - timedelta(days=days_back)).timestamp())
    stories: dict[str, LayoffStory] = {}

    for query in HN_QUERIES:
        try:
            resp = requests.get(
                HN_SEARCH_URL,
                params={"query": query, "tags": "story",
                        "numericFilters": f"created_at_i>{cutoff_ts}",
                        "hitsPerPage": max_per_query},
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.warning(f"HN query '{query}' fallita: {e}")
            continue

        for hit in data.get("hits", []):
            obj_id = hit.get("objectID")
            title = hit.get("title") or ""
            url = hit.get("url") or ""
            created_at = hit.get("created_at")
            if not obj_id or not title or not created_at or obj_id in stories:
                continue
            company = _extract_company(title)
            if not _is_valid_story(title, company):
                continue
            try:
                date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            stories[obj_id] = LayoffStory(
                company=company, title=title, url=url, date=date,
                source="Hacker News",
                employees=_extract_employees(title),
                percent_workforce=_extract_percent(title),
                ai_cause=_ai_cause_level(title, url),
                hn_url=f"https://news.ycombinator.com/item?id={obj_id}",
                hn_points=hit.get("points", 0) or 0,
            )
    return list(stories.values())


def _parse_rss_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(date_str[:25], fmt[:len(date_str[:25])])
        except ValueError:
            continue
    return None


def _fetch_rss(source_name: str, url: str, days_back: int) -> list[LayoffStory]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
    stories = []
    seen: set[str] = set()

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        st.warning(f"RSS '{source_name}' fallita: {e}")
        return []

    ns = {"dc": "http://purl.org/dc/elements/1.1/"}

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "")

        # Google News wraps link in CDATA after <link> tag
        if not link:
            link = item.findtext("{http://www.w3.org/2005/Atom}link", "")

        dedup_key = link or title
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        date = _parse_rss_date(pub_date)
        if date is None:
            continue
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        if date < cutoff:
            continue

        company = _extract_company(title)
        if not _is_valid_story(title, company):
            continue

        stories.append(LayoffStory(
            company=company, title=title, url=link, date=date,
            source=source_name,
            employees=_extract_employees(title),
            percent_workforce=_extract_percent(title),
            ai_cause=_ai_cause_level(title, link),
        ))
    return stories


# --- Public API ---

def _get_all_rss_sources() -> dict[str, str]:
    """Unisce le RSS hardcoded con quelle custom registrate in Firestore.

    Le custom NON sovrascrivono le hardcoded se hanno lo stesso nome
    (l'add ne previene la creazione comunque). In caso di errore Firestore,
    si torna sulle sole hardcoded.
    """
    merged = dict(RSS_SOURCES)
    try:
        from db import get_custom_sources
        for s in get_custom_sources(include_disabled=False):
            name = s.get("name")
            url = s.get("url")
            if name and url and name not in merged:
                merged[name] = url
    except Exception as e:
        # Non bloccare l'ETL se Firestore è temporaneamente down.
        try:
            st.warning(f"Impossibile leggere fonti custom da Firestore: {e}")
        except Exception:
            print(f"[scraper] custom sources unavailable: {e}")
    return merged


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_all_sources(days_back: int = 90) -> pd.DataFrame:
    """Fetch from all sources (HN + RSS hardcoded + RSS custom) and merge
    into one deduplicated DataFrame.

    Returns DataFrame sorted by date descending.
    Empty DataFrame if all sources fail.
    """
    all_stories: list[LayoffStory] = []

    with st.spinner("Hacker News…"):
        all_stories += _fetch_hn(days_back=days_back, max_per_query=100)

    rss_sources = _get_all_rss_sources()
    for source_name, rss_url in rss_sources.items():
        with st.spinner(f"{source_name}…"):
            all_stories += _fetch_rss(source_name, rss_url, days_back)

    if not all_stories:
        return pd.DataFrame()

    df = pd.DataFrame([s.to_row() for s in all_stories])

    # Deduplicate by title similarity: keep first occurrence per (company, date)
    df["_title_key"] = df["title"].str.lower().str[:60]
    df = df.drop_duplicates(subset=["_title_key"]).drop(columns=["_title_key"])

    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def filter_ai_related(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows where title or URL mentions an AI keyword."""
    if df.empty:
        return df
    mask = df.apply(lambda r: _is_ai_related(r["title"], r.get("url") or ""), axis=1)
    return df[mask].reset_index(drop=True)
