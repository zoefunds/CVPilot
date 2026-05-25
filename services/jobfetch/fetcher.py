"""
Fetch a job posting URL and return visible text + title.
Guarded by:
  - 10s connect / 15s read timeout
  - 2 MB response cap
  - text/html content type required
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from backend.app.core.errors import ValidationAppError

_MAX_BYTES = 2 * 1024 * 1024
_USER_AGENT = "CVPilotBot/0.1 (+https://cvpilot.dev)"


@dataclass(frozen=True)
class JobPosting:
    url: str
    final_url: str
    title: str
    text: str


def _clean_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or ""

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse blank-line runs
    lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]
    return title, "\n".join(lines)


def fetch_job_posting(url: str) -> JobPosting:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=5.0),
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html,*/*"},
        ) as client:
            r = client.get(url)
    except httpx.HTTPError as exc:
        raise ValidationAppError(
            f"Could not reach job URL: {exc.__class__.__name__}",
            code="job_url_unreachable",
        ) from exc

    if r.status_code >= 400:
        raise ValidationAppError(
            f"Job URL returned HTTP {r.status_code}.",
            code="job_url_http_error",
        )

    ctype = r.headers.get("content-type", "")
    if "text/html" not in ctype and "application/xhtml" not in ctype:
        raise ValidationAppError(
            f"Job URL did not return HTML (content-type={ctype}).",
            code="job_url_not_html",
        )

    content = r.content[:_MAX_BYTES]
    title, text = _clean_html(content.decode("utf-8", errors="ignore"))
    if not text:
        raise ValidationAppError(
            "Could not extract any text from the job posting.",
            code="job_url_empty",
        )

    return JobPosting(url=url, final_url=str(r.url), title=title, text=text)
