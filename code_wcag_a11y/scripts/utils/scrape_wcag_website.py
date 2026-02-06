import json
import requests
from bs4 import BeautifulSoup
import re

from code_wcag_a11y.globals import BENEFITS_CACHE_FILE
from code_wcag_a11y.scripts.types.chunk_types import WcagVersion


def get_sc_url(base_url: str, id: str, wcag_version: WcagVersion) -> str:
    return f"{base_url}/WCAG{wcag_version.replace('.','')}/Understanding/{id}.html"


def get_user_benefits_from_rule_page(url: str) -> list[str]:
    # TODO: This is a very basic implementation. The structure of the WCAG Understanding pages can vary, so this may need to be adjusted to reliably extract benefits across different pages.
    # IF THE ENHANCED HAS 0 BENEFITS USE THE ONES FOR THE MINIMUM

    # TODO - enable caching and also only add benefits to Wcag2.2 new rules. For the rules that are the same as in 2.1 recycle the benefits
    try:
        page = requests.get(url)
        page.raise_for_status()  # Ensure the request worked

        soup = BeautifulSoup(page.content, "html.parser")

        # The WCAG 'Understanding' pages usually put benefits in a section
        # with id="benefits" or a heading.
        benefits_section = soup.find(id="benefits")

        if not benefits_section:
            return []

        # Find the list items (li) within that section
        # We exclude items that are just "markers" or empty pseudo-content
        benefits = []

        for li in benefits_section.find_all("li"):

            # This is where we strictly filter the pseudo-content
            if "marker" in li.get("class", []) or "pseudocontent" in li.get(
                "class", []
            ):
                continue

            raw_text = li.get_text(separator=" ", strip=True)
            clean_text = re.sub(r"\s+", " ", raw_text)
            if clean_text and clean_text.lower() != "none":
                benefits.append(clean_text)

        return benefits

    except Exception as e:
        print(f"Error scraping benefits: {e}")
        return []


def load_benefits_cache() -> dict[str, list[str]]:
    """Load already scraped benefits from disk."""
    if BENEFITS_CACHE_FILE.exists():
        with open(BENEFITS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_benefits_cache(cache: dict):
    """Save new scraped benefits to disk for next time."""
    with open(BENEFITS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
