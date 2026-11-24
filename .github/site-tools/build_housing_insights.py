"""Render the curated Housing Insights JSON into standalone accessible HTML."""

from __future__ import annotations

from datetime import date
from html import escape
import json
from pathlib import Path
from urllib.parse import urlparse


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Expected an HTTPS source URL, got {value!r}")
    return escape(value, quote=True)


def valid_date(value: str) -> str:
    date.fromisoformat(value)
    return escape(value)


def display_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def render_cards(data: dict) -> dict[str, str]:
    stats = []
    for item in data["statistics"]:
        stats.append(
            '<article class="insight-card insight-stat-card">'
            f'<p class="insight-stat-value">{escape(item["value"])}</p>'
            f'<h3>{escape(item["title"])}</h3>'
            f'<p>{escape(item["description"])}</p>'
            '<dl class="insight-source-details">'
            f'<div><dt>Geography</dt><dd>{escape(item["geographicScope"])}</dd></div>'
            f'<div><dt>Period</dt><dd>{escape(item["reportingPeriod"])}</dd></div>'
            f'<div><dt>Source</dt><dd><a href="{safe_url(item["sourceUrl"])}" target="_blank" rel="noopener noreferrer">{escape(item["sourceOrganization"])} (verified {valid_date(item["lastVerified"])})</a></dd></div>'
            '</dl></article>'
        )

    progress = []
    for item in data["progress"]:
        progress.append(
            '<article class="insight-card insight-progress-card">'
            f'<p class="insight-progress-value">{escape(item["value"])}</p>'
            f'<h3>{escape(item["title"])}</h3>'
            f'<p>{escape(item["description"])}</p>'
            '<dl class="insight-source-details">'
            f'<div><dt>Geography</dt><dd>{escape(item["geographicScope"])}</dd></div>'
            f'<div><dt>Reported</dt><dd>{escape(item["reportingPeriod"])}</dd></div>'
            f'<div><dt>Source</dt><dd><a href="{safe_url(item["sourceUrl"])}" target="_blank" rel="noopener noreferrer">{escape(item["sourceOrganization"])} (verified {valid_date(item["lastVerified"])})</a></dd></div>'
            '</dl></article>'
        )

    articles = []
    for item in data["articles"]:
        published = valid_date(item["publicationDate"])
        articles.append(
            '<article class="insight-card insight-article-card">'
            f'<p class="eyebrow">{escape(item["publication"])}</p>'
            f'<h3>{escape(item["title"])}</h3>'
            f'<p class="insight-article-date"><time datetime="{published}">{escape(display_date(item["publicationDate"]))}</time></p>'
            f'<p>{escape(item["summary"])}</p>'
            f'<p class="insight-source-note">Source verified {valid_date(item["lastVerified"])}</p>'
            f'<a class="resource-link" href="{safe_url(item["sourceUrl"])}" target="_blank" rel="noopener noreferrer">Read the original story<span aria-hidden="true"> &#8599;</span></a>'
            '</article>'
        )

    return {
        "{{LAST_UPDATED}}": valid_date(data["lastUpdated"]),
        "{{LAST_UPDATED_DISPLAY}}": escape(display_date(data["lastUpdated"])),
        "{{STATISTICS}}": "\n".join(stats),
        "{{PROGRESS}}": "\n".join(progress),
        "{{ARTICLES}}": "\n".join(articles),
    }


def build_page(data_path: Path, template_path: Path, output_path: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if len(data.get("statistics", [])) < 3:
        raise ValueError("Housing Insights must include at least three reviewed statistics")
    if not data.get("articles") or not data.get("progress"):
        raise ValueError("Housing Insights needs at least one article and one progress example")
    for field in ("lastUpdated",):
        valid_date(data[field])
    html = template_path.read_text(encoding="utf-8")
    for token, value in render_cards(data).items():
        html = html.replace(token, value)
    if "{{" in html or "}}" in html:
        raise ValueError("Unresolved template token in Housing Insights page")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8", newline="\n")

