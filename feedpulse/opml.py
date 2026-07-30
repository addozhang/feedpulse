from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from xml.etree import ElementTree

MAX_OPML_FEEDS = 1000


def parse_opml(content: bytes) -> list[dict[str, str]]:
    """Parse unique feed URLs and titles from an OPML document."""
    root = ElementTree.fromstring(content)
    if root.tag.rsplit("}", 1)[-1].lower() != "opml":
        raise ValueError("document root is not OPML")

    feeds = []
    seen_urls = set()
    for outline in root.iter():
        if outline.tag.rsplit("}", 1)[-1].lower() != "outline":
            continue
        url = (outline.get("xmlUrl") or outline.get("xmlurl") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        feeds.append(
            {
                "url": url,
                "title": (outline.get("title") or outline.get("text") or url).strip(),
            }
        )
        if len(feeds) > MAX_OPML_FEEDS:
            raise ValueError(f"OPML contains more than {MAX_OPML_FEEDS} feeds")
    return feeds


def build_opml(feeds: Iterable[Mapping[str, object]]) -> bytes:
    """Build an OPML 2.0 document from feed rows."""
    root = ElementTree.Element("opml", version="2.0")
    head = ElementTree.SubElement(root, "head")
    ElementTree.SubElement(head, "title").text = "FeedPulse subscriptions"
    ElementTree.SubElement(head, "dateCreated").text = datetime.now(UTC).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )
    body = ElementTree.SubElement(root, "body")
    for feed in feeds:
        url = str(feed["url"])
        title = str(feed["title"] or url)
        ElementTree.SubElement(
            body,
            "outline",
            text=title,
            title=title,
            type="rss",
            xmlUrl=url,
        )
    ElementTree.indent(root, space="  ")
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
