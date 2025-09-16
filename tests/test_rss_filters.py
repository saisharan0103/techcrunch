from datetime import datetime, timezone

from src.rss import FeedItem, build_paged_url, filter_items_for_date


def test_filter_items_for_date_matches_timezone():
    items = [
        FeedItem(
            title="A",
            link="https://example.com/a",
            summary="",
            published=datetime(2025, 9, 15, 18, 30, tzinfo=timezone.utc),
        ),
        FeedItem(
            title="B",
            link="https://example.com/b",
            summary="",
            published=datetime(2025, 9, 15, 10, 0, tzinfo=timezone.utc),
        ),
    ]
    target_date = datetime(2025, 9, 16, tzinfo=timezone.utc).date()
    filtered = filter_items_for_date(items, target_date=target_date, tz_name="Asia/Kolkata")
    assert len(filtered) == 1
    assert filtered[0].title == "A"


def test_build_paged_url_adds_query_param():
    base = "https://techcrunch.com/feed/"
    assert build_paged_url(base, 1) == base
    assert build_paged_url(base, 3) == "https://techcrunch.com/feed/?paged=3"


def test_build_paged_url_preserves_existing_query():
    base = "https://example.com/feed/?foo=bar"
    assert build_paged_url(base, 2) in {
        "https://example.com/feed/?foo=bar&paged=2",
        "https://example.com/feed/?paged=2&foo=bar",
    }
