"""
Extract structured job fields from raw HTML.
Strategy: JSON-LD JobPosting -> Open Graph -> heuristic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

_MAX_DESC = 4000


@dataclass(frozen=True)
class ExtractedJob:
    url: str
    title: str | None
    company: str | None
    location: str | None
    employment_type: str | None
    description: str | None


def _txt(s: str | None) -> str | None:
    if not isinstance(s, str):
        return None
    s = s.strip()
    return s or None


def _flatten_str(value: Any) -> str | None:
    if isinstance(value, str):
        return _txt(value)
    if isinstance(value, dict):
        return _flatten_str(value.get("name") or value.get("@value"))
    if isinstance(value, list):
        for v in value:
            r = _flatten_str(v)
            if r:
                return r
    return None


def _extract_jsonld(soup: BeautifulSoup) -> dict | None:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                return item
    return None


def _location_from_jsonld(jl: Any) -> str | None:
    if isinstance(jl, list) and jl:
        jl = jl[0]
    if not isinstance(jl, dict):
        return None
    addr = jl.get("address")
    if not isinstance(addr, dict):
        return _flatten_str(jl.get("name"))
    parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
    cleaned = [p for p in parts if isinstance(p, str) and p.strip()]
    return ", ".join(cleaned) if cleaned else None


def _strip_inline_html(s: str | None) -> str | None:
    if not s:
        return None
    if "<" not in s or ">" not in s:
        return s.strip() or None
    return BeautifulSoup(s, "lxml").get_text(separator="\n", strip=True) or None


def _from_meta(soup: BeautifulSoup) -> dict:
    out: dict = {}
    for prop in ("og:title", "og:site_name", "og:description"):
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            out[prop] = tag["content"].strip()
    return out


def _heuristic_description(soup: BeautifulSoup) -> str | None:
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    if not text:
        return None
    return text[:_MAX_DESC].strip() or None


def extract_job_fields(html: str, url: str, fallback_title: str | None = None) -> ExtractedJob:
    soup = BeautifulSoup(html or "", "lxml")
    ld = _extract_jsonld(soup)
    if ld:
        company = None
        org = ld.get("hiringOrganization")
        if isinstance(org, dict):
            company = _flatten_str(org.get("name"))
        elif isinstance(org, str):
            company = _txt(org)
        location = _location_from_jsonld(ld.get("jobLocation"))
        description = _strip_inline_html(_flatten_str(ld.get("description")))
        if description and len(description) > _MAX_DESC:
            description = description[:_MAX_DESC]
        return ExtractedJob(
            url=url,
            title=_flatten_str(ld.get("title")) or fallback_title,
            company=company,
            location=location,
            employment_type=_flatten_str(ld.get("employmentType")),
            description=description,
        )
    meta = _from_meta(soup)
    description = meta.get("og:description") or _heuristic_description(soup)
    if description and len(description) > _MAX_DESC:
        description = description[:_MAX_DESC]
    return ExtractedJob(
        url=url,
        title=meta.get("og:title") or fallback_title,
        company=meta.get("og:site_name"),
        location=None,
        employment_type=None,
        description=description,
    )
