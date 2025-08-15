from __future__ import annotations

from typing import Dict, Iterable, List

from intel_analysis_service.nlp import classify_sentiment, detect_threat
from yosai_intel_dashboard.src.database import social_signals


def stream_twitter(
    tweets: Iterable[Dict[str, str]], location_filter: str
) -> List[social_signals.SocialSignal]:
    """Process a stream of tweets filtered by location."""
    alerts: List[social_signals.SocialSignal] = []
    for tweet in tweets:
        if tweet.get("location") != location_filter:
            continue
        text = tweet.get("text", "")
        sentiment = classify_sentiment(text)
        threat = detect_threat(text)
        alert = social_signals.SocialSignal(
            source="twitter",
            text=text,
            location=tweet.get("location", ""),
            sentiment=sentiment,
            threat=threat,
        )
        social_signals.save_alert(alert)
        alerts.append(alert)
    return alerts
