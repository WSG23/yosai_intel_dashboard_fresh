from __future__ import annotations

from typing import Dict, Iterable, List

from intel_analysis_service.nlp import classify_sentiment, detect_threat
from yosai_intel_dashboard.src.database import social_signals


def ingest_rss(
    items: Iterable[Dict[str, str]], location_filter: str
) -> List[social_signals.SocialSignal]:
    """Ingest RSS feed items filtered by location."""
    alerts: List[social_signals.SocialSignal] = []
    for item in items:
        if item.get("location") != location_filter:
            continue
        text = item.get("text", "")
        sentiment = classify_sentiment(text)
        threat = detect_threat(text)
        alert = social_signals.SocialSignal(
            source="rss",
            text=text,
            location=item.get("location", ""),
            sentiment=sentiment,
            threat=threat,
        )
        social_signals.save_alert(alert)
        alerts.append(alert)
    return alerts
