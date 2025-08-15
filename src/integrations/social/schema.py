from __future__ import annotations

from typing import List

import strawberry

from yosai_intel_dashboard.src.database import social_signals


@strawberry.type
class SocialSignalType:
    source: str
    text: str
    location: str
    sentiment: str
    threat: bool


@strawberry.type
class Query:
    @strawberry.field(name="socialSignals")
    def resolve_social_signals(self) -> List[SocialSignalType]:
        return social_signals.list_alerts()


schema = strawberry.Schema(Query)
