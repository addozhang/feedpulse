from xml.etree import ElementTree

import pytest

from feedpulse.opml import MAX_OPML_FEEDS, build_opml, parse_opml


def test_build_and_parse_opml():
    content = build_opml(
        [
            {"title": "Example & News", "url": "https://example.com/feed.xml"},
            {"title": None, "url": "https://example.org/rss"},
        ]
    )

    root = ElementTree.fromstring(content)
    assert root.tag == "opml"
    assert root.attrib["version"] == "2.0"
    assert parse_opml(content) == [
        {"title": "Example & News", "url": "https://example.com/feed.xml"},
        {"title": "https://example.org/rss", "url": "https://example.org/rss"},
    ]


def test_parse_nested_opml_deduplicates_urls():
    content = b"""<?xml version="1.0"?>
    <opml version="2.0"><body><outline text="Tech">
      <outline text="One" xmlUrl="https://example.com/rss" />
      <outline title="Duplicate" xmlUrl="https://example.com/rss" />
    </outline></body></opml>"""

    assert parse_opml(content) == [
        {"title": "One", "url": "https://example.com/rss"}
    ]


def test_parse_rejects_non_opml_document():
    with pytest.raises(ValueError, match="root is not OPML"):
        parse_opml(b"<rss />")


def test_parse_rejects_too_many_feeds():
    outlines = "".join(
        f'<outline xmlUrl="https://example.com/{index}" />'
        for index in range(MAX_OPML_FEEDS + 1)
    )

    with pytest.raises(ValueError, match="more than"):
        parse_opml(f"<opml><body>{outlines}</body></opml>".encode())
