"""
Small helpers for turning a raw model response into what the API returns.

Unlike the earlier WordPress project, this backend has only ONE client (the
Android app), so we don't need an HTML-formatting function — the mobile
client renders Markdown natively (including ```python code blocks) with a
library like Markwon. We just need to pull out any raw links so the app can
show them as native buttons instead of clickable text.
"""

import re

DEFAULT_LINK_TITLE = "مشاهده اطلاعات بیشتر"


def extract_links(text: str) -> list[dict]:
    """
    Finds raw URLs in the model's response and returns them as a separate
    list, so the mobile app can render them as native buttons instead of
    parsing links out of Markdown text itself.
    """
    urls = re.findall(r"https?://[^\s<>\"]+", text)

    seen = set()
    links = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            links.append({"title": DEFAULT_LINK_TITLE, "url": url})
    return links
