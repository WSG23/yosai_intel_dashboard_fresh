"""AI-assisted column mapping with fuzzy standardization."""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from components.plugin_adapter import ComponentPluginAdapter

# ---------------------------------------------------------------------------
# Header variant dictionaries
# ---------------------------------------------------------------------------

ENGLISH_COLUMNS: Dict[str, List[str]] = {
    "timestamp": [
        "timestamp",
        "time",
        "date",
        "datetime",
        "event_time",
        "created_at",
    ],
    "person_id": [
        "person id",
        "person",
        "user",
        "user id",
        "employee",
        "badge",
        "card_id",
    ],
    "door_id": [
        "door",
        "door id",
        "device",
        "device name",
        "reader",
        "location",
        "access_point",
    ],
    "access_result": [
        "access result",
        "result",
        "status",
        "outcome",
        "decision",
    ],
    "direction": [
        "direction",
        "entry_exit",
        "in_out",
    ],
    "floor": ["floor", "level"],
    "zone_id": ["zone", "zone id"],
    "facility_id": ["facility", "facility id", "building"],
    "token_id": ["token id", "badge id", "card id"],
    "event_type": ["event type", "type", "category"],
}

JAPANESE_COLUMNS: Dict[str, List[str]] = {
    "timestamp": ["タイムスタンプ", "日時", "時間", "日付", "発生時刻"],
    "person_id": ["利用者ID", "ユーザーID", "従業員ID", "人物ID"],
    "door_id": ["ドアID", "デバイス名", "場所ID", "ドア名", "リーダーID"],
    "access_result": ["アクセス結果", "結果", "ステータス", "認証結果"],
    "direction": ["方向", "入出", "進行方向"],
    "floor": ["階", "フロア", "階数"],
    "zone_id": ["ゾーンID", "領域ID", "エリアID"],
    "facility_id": ["施設ID", "建物ID", "ビルID"],
    "token_id": ["トークンID", "カードID", "バッジID", "識別子"],
    "event_type": ["イベントタイプ", "種類", "イベント種別"],
}

# ---------------------------------------------------------------------------
# Standardization helpers
# ---------------------------------------------------------------------------

def standardize_column_names(
    df: pd.DataFrame,
    custom_mappings: Optional[Dict[str, List[str]]] = None,
    use_japanese: bool = False,
) -> pd.DataFrame:
    """Return ``df`` with columns renamed to canonical headers."""

    mappings: Dict[str, List[str]] = {**ENGLISH_COLUMNS}
    if use_japanese:
        for key, vals in JAPANESE_COLUMNS.items():
            mappings.setdefault(key, []).extend(vals)
    if custom_mappings:
        for key, vals in custom_mappings.items():
            mappings.setdefault(key, []).extend(vals)

    reverse: Dict[str, str] = {}
    for canon, aliases in mappings.items():
        reverse[canon.lower()] = canon
        for alias in aliases:
            reverse[str(alias).lower()] = canon

    renamed: Dict[str, str] = {}
    for col in df.columns:
        target = reverse.get(str(col).lower())
        if target:
            renamed[col] = target

    if renamed:
        df = df.rename(columns=renamed)
    return df


class AIColumnMapperAdapter:
    """Combine AI suggestions with fuzzy header standardization."""

    def __init__(
        self,
        ai_adapter: ComponentPluginAdapter,
        custom_mappings: Optional[Dict[str, List[str]]] = None,
        use_japanese: bool = False,
    ) -> None:
        self.ai_adapter = ai_adapter
        self.custom_mappings = custom_mappings
        self.use_japanese = use_japanese

    def map_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        suggestions = self.ai_adapter.suggest_columns(df)
        df = df.rename(columns=suggestions)
        return standardize_column_names(
            df, custom_mappings=self.custom_mappings, use_japanese=self.use_japanese
        )


if __name__ == "__main__":
    import pandas as pd
    from example_ai_adapter import ComponentPluginAdapter

    data = {
        "Time": ["2023-01-01 12:00"],
        "利用者ID": ["A1"],
        "Door Name": ["D1"],
        "結果": ["Granted"],
    }
    frame = pd.DataFrame(data)
    mapper = AIColumnMapperAdapter(ComponentPluginAdapter(), use_japanese=True)
    result = mapper.map_and_standardize(frame)
    print(result.columns.tolist())
