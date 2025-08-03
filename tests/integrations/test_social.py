from __future__ import annotations

import pathlib
import sys

# make intel_analysis_service package available
sys.path.append(
    str(pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src" / "services")
)

from database import social_signals
from integrations.social import reddit, rss, schema, twitter


def setup_function() -> None:
    social_signals.clear_alerts()


def test_twitter_stream_classification() -> None:
    tweets = [
        {"text": "good day", "location": "SF"},
        {"text": "bad attack", "location": "SF"},
        {"text": "great", "location": "LA"},
    ]
    alerts = twitter.stream_twitter(tweets, "SF")
    assert len(alerts) == 2
    assert alerts[0].sentiment == "positive"
    assert alerts[1].sentiment == "negative" and alerts[1].threat is True
    stored = social_signals.list_alerts()
    assert len(stored) == 2 and all(a.location == "SF" for a in stored)


def test_rss_and_reddit_ingestion() -> None:
    rss_items = [{"text": "bad weather", "location": "NY"}]
    reddit_posts = [{"text": "love this", "location": "NY"}]
    rss_alerts = rss.ingest_rss(rss_items, "NY")
    reddit_alerts = reddit.scrape_reddit(reddit_posts, "NY")
    assert rss_alerts[0].sentiment == "negative"
    assert reddit_alerts[0].sentiment == "positive"
    assert len(social_signals.list_alerts()) == 2


def test_graphql_resolver_exposes_alerts() -> None:
    twitter.stream_twitter([{"text": "attack now", "location": "TX"}], "TX")
    query = "{ socialSignals { source text location sentiment threat } }"
    result = schema.schema.execute_sync(query)
    assert not result.errors
    data = result.data["socialSignals"]
    assert len(data) == 1 and data[0]["threat"] is True
