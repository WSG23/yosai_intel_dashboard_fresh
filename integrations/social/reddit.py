from __future__ import annotations

from typing import Dict, Iterable, List

from intel_analysis_service.nlp import classify_sentiment, detect_threat
from database import social_signals


def scrape_reddit(
    posts: Iterable[Dict[str, str]], location_filter: str
) -> List[social_signals.SocialSignal]:
    """Scrape Reddit posts filtered by location."""
    alerts: List[social_signals.SocialSignal] = []
    for post in posts:
        if post.get("location") != location_filter:
            continue
        text = post.get("text", "")
        sentiment = classify_sentiment(text)
        threat = detect_threat(text)
        alert = social_signals.SocialSignal(
            source="reddit",
            text=text,
            location=post.get("location", ""),
            sentiment=sentiment,
            threat=threat,
        )
        social_signals.save_alert(alert)
        alerts.append(alert)
    return alerts
