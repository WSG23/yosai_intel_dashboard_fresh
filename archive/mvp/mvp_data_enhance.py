#!/usr/bin/env python3
"""Single page data enhancement tool for MVP demos."""
from __future__ import annotations

import base64
import io
import json
from datetime import datetime
from typing import Any, Dict, List

import dash_bootstrap_components as dbc
import pandas as pd
from dash import (
    ALL,
    Dash,
    Input,
    Output,
    State,
    callback_context,
    dash_table,
    dcc,
    html,
    no_update,
)
from flask import Flask

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from mvp.unicode_fix_module import sanitize_dataframe

# ---------------------------------------------------------------------------
# Safe imports with fallbacks

try:
    from services.data_enhancer import get_ai_column_suggestions
except Exception:

    def get_ai_column_suggestions(columns: List[str]) -> Dict[str, Dict[str, Any]]:
        """Simplistic heuristic suggestions."""
        suggestions: Dict[str, Dict[str, Any]] = {}
        for col in columns:
            col_lower = col.lower()
            field = ""
            conf = 0.0
            if any(k in col_lower for k in ["person", "user", "employee", "name"]):
                field, conf = "person_id", 0.7
            elif any(k in col_lower for k in ["door", "location", "device", "room"]):
                field, conf = "door_id", 0.7
            elif any(k in col_lower for k in ["time", "date", "stamp"]):
                field, conf = "timestamp", 0.8
            elif any(k in col_lower for k in ["result", "status", "access"]):
                field, conf = "access_result", 0.7
            elif any(k in col_lower for k in ["token", "badge", "card"]):
                field, conf = "token_id", 0.6
            suggestions[col] = {"field": field, "confidence": conf}
        return suggestions


try:
    from services.configuration_service import ConfigurationServiceProtocol
    from services.door_mapping_service import DoorMappingService

    from core.config import get_ai_confidence_threshold

    class _MockCfg(ConfigurationServiceProtocol):
        def get_ai_confidence_threshold(self) -> float:  # type: ignore[override]
            return get_ai_confidence_threshold()

    DEVICE_SERVICE = DoorMappingService(_MockCfg())
except Exception:

    class _FallbackDoorService:
        def process_uploaded_data(
            self, df: pd.DataFrame, client_profile: str = "auto"
        ) -> Dict[str, Any]:
            mappings = []
            device_col = None
            for c in df.columns:
                if "door" in c.lower() or "device" in c.lower():
                    device_col = c
                    break
            if device_col is None:
                return {"devices": [], "ai_model_version": "fallback"}
            for dev in df[device_col].dropna().unique()[:50]:
                dev_str = str(dev)
                mappings.append(
                    {
                        "door_id": dev_str,
                        "floor_number": 1,
                        "security_level": 5,
                        "is_entry": True,
                        "is_exit": False,
                        "is_elevator": "elevator" in dev_str.lower(),
                        "is_stairwell": "stair" in dev_str.lower(),
                        "is_fire_escape": "fire" in dev_str.lower(),
                        "is_restricted": "restricted" in dev_str.lower(),
                        "confidence": 60,
                    }
                )
            return {"devices": mappings, "ai_model_version": "fallback"}

    DEVICE_SERVICE = _FallbackDoorService()

# ---------------------------------------------------------------------------
# Helper utilities

_SUR_START = 0xD800
_SUR_END = 0xDFFF


def _remove_surrogates(text: str) -> str:
    return "".join(ch for ch in text if not (_SUR_START <= ord(ch) <= _SUR_END))


def parse_contents(contents: str, filename: str) -> pd.DataFrame:
    """Parse uploaded file contents with multiple encodings."""
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    if filename.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(io.BytesIO(decoded))
    else:
        encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252", "iso-8859-1"]
        df = None
        for enc in encodings:
            try:
                text = decoded.decode(enc, errors="replace")
                text = _remove_surrogates(text)
                if filename.lower().endswith(".json"):
                    data = json.loads(text)
                    df = pd.DataFrame(data if isinstance(data, list) else [data])
                else:
                    df = pd.read_csv(io.StringIO(text))
                break
            except Exception:
                df = None
                continue
        if df is None:
            raise ValueError("Unable to decode uploaded file")

    df.columns = [_remove_surrogates(str(c)).strip() for c in df.columns]
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).apply(_remove_surrogates)
    df = sanitize_dataframe(df)
    return df


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    rename = {src: tgt for src, tgt in mapping.items() if tgt}
    if rename:
        df = df.rename(columns=rename)
    return df


def apply_device_mapping(
    df: pd.DataFrame, devices: List[Dict[str, Any]]
) -> pd.DataFrame:
    if not devices or "door_id" not in df.columns:
        return df
    look = {str(d["door_id"]): d for d in devices}
    df["floor_number"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("floor_number"))
    )
    df["security_level"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("security_level"))
    )
    df["is_entry"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_entry"))
    )
    df["is_exit"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_exit"))
    )
    df["is_elevator"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_elevator"))
    )
    df["is_stairwell"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_stairwell"))
    )
    df["is_fire_escape"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_fire_escape"))
    )
    df["is_restricted"] = (
        df["door_id"].astype(str).map(lambda x: look.get(x, {}).get("is_restricted"))
    )
    return df


# ---------------------------------------------------------------------------
# Global session state

SESSION: Dict[str, Any] = {
    "raw_df": None,
    "enhanced_df": None,
    "column_mapping": {},
    "device_mapping": [],
    "filename": None,
    "stage": "upload",
}


# ---------------------------------------------------------------------------
# Layout builders


def layout_upload() -> html.Div:
    return html.Div(
        [
            html.H3("Step 1: Upload File", className="text-light"),
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={
                    "width": "100%",
                    "height": "150px",
                    "lineHeight": "150px",
                    "borderWidth": "2px",
                    "borderStyle": "dashed",
                    "borderRadius": "10px",
                    "textAlign": "center",
                    "background": "linear-gradient(45deg, #e0eafc, #cfdef3)",
                },
            ),
        ]
    )


def layout_preview(df: pd.DataFrame) -> html.Div:
    return html.Div(
        [
            html.H3("Step 2: Preview Data"),
            html.P(f"Rows: {len(df)} Columns: {len(df.columns)}"),
            dash_table.DataTable(
                data=df.head().to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                style_table={"overflowX": "auto"},
                page_size=5,
            ),
            html.Br(),
            dbc.Button("Next: Column Mapping", id="to-mapping", color="primary"),
        ]
    )


def layout_column_mapping(df: pd.DataFrame) -> html.Div:
    ai = get_ai_column_suggestions(list(df.columns))
    options = [
        {"label": "Not Mapped", "value": ""},
        {"label": "person_id", "value": "person_id"},
        {"label": "door_id", "value": "door_id"},
        {"label": "access_result", "value": "access_result"},
        {"label": "timestamp", "value": "timestamp"},
        {"label": "token_id", "value": "token_id"},
        {"label": "event_type", "value": "event_type"},
    ]
    cards = []
    for col in df.columns:
        sug = ai.get(col, {})
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H6(f"Column: {col}"),
                            html.Small(
                                f"AI: {sug.get('field', '')} "
                                f"({sug.get('confidence', 0) * 100:.0f}%)"
                            ),
                            dcc.Dropdown(
                                id={"type": "map-col", "index": col},
                                options=options,
                                value=sug.get("field", ""),
                                placeholder="Select mapping",
                            ),
                        ]
                    )
                ],
                className="mb-2",
            )
        )
    return html.Div(
        [
            html.H3("Step 3: Column Mapping"),
            html.Div(cards),
            dbc.Button("Next: Device Mapping", id="to-device", color="primary"),
        ]
    )


def layout_device_mapping(df: pd.DataFrame) -> html.Div:
    mapped = apply_column_mapping(df, SESSION["column_mapping"])
    try:
        result = DEVICE_SERVICE.process_uploaded_data(mapped)
        ai_devices = {d["door_id"]: d for d in result.get("devices", [])}
    except Exception:
        ai_devices = {}
    devices = list(
        mapped.get("door_id", mapped.iloc[:, 0]).dropna().astype(str).unique()
    )[:10]
    cards = []
    for d in devices:
        info = ai_devices.get(d, {})
        cards.append(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(f"Device: {d}"),
                        html.Small(
                            f"AI confidence: {info.get('confidence', 0)}%"
                            if info
                            else ""
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Input(
                                        id={"type": "dev-floor", "index": d},
                                        type="number",
                                        value=info.get("floor_number", 1),
                                        min=1,
                                        max=50,
                                    ),
                                    width=3,
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id={"type": "dev-sec", "index": d},
                                        type="number",
                                        value=info.get("security_level", 5),
                                        min=1,
                                        max=10,
                                    ),
                                    width=3,
                                ),
                                dbc.Col(
                                    dcc.Checklist(
                                        id={"type": "dev-access", "index": d},
                                        options=[
                                            {"label": "Entry", "value": "entry"},
                                            {"label": "Exit", "value": "exit"},
                                        ],
                                        value=[
                                            *("entry" if info.get("is_entry") else []),
                                            *("exit" if info.get("is_exit") else []),
                                        ],
                                    ),
                                    width=3,
                                ),
                                dbc.Col(
                                    dcc.Checklist(
                                        id={"type": "dev-spec", "index": d},
                                        options=[
                                            {
                                                "label": "Elevator",
                                                "value": "is_elevator",
                                            },
                                            {
                                                "label": "Stairwell",
                                                "value": "is_stairwell",
                                            },
                                            {
                                                "label": "Fire",
                                                "value": "is_fire_escape",
                                            },
                                            {
                                                "label": "Restricted",
                                                "value": "is_restricted",
                                            },
                                        ],
                                        value=[
                                            *(
                                                "is_elevator"
                                                if info.get("is_elevator")
                                                else []
                                            ),
                                            *(
                                                "is_stairwell"
                                                if info.get("is_stairwell")
                                                else []
                                            ),
                                            *(
                                                "is_fire_escape"
                                                if info.get("is_fire_escape")
                                                else []
                                            ),
                                            *(
                                                "is_restricted"
                                                if info.get("is_restricted")
                                                else []
                                            ),
                                        ],
                                    ),
                                    width=3,
                                ),
                            ]
                        ),
                    ]
                ),
                className="mb-2",
            )
        )
    return html.Div(
        [
            html.H3("Step 4: Device Mapping"),
            html.Div(cards),
            dbc.Button("Next: Enhance Data", id="to-enhance", color="primary"),
        ]
    )


def layout_enhanced(df: pd.DataFrame, original_cols: List[str]) -> html.Div:
    new_cols = [c for c in df.columns if c not in original_cols]
    return html.Div(
        [
            html.H3("Step 5: Enhanced Data"),
            html.P(
                "Original columns: "
                f"{len(original_cols)} | Enhanced columns: {len(df.columns)}"
            ),
            dash_table.DataTable(
                data=df.head().to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                style_data_conditional=[
                    {"if": {"column_id": c}, "backgroundColor": "#e8f7e4"}
                    for c in new_cols
                ],
            ),
            html.Br(),
            dbc.ButtonGroup(
                [
                    dbc.Button("Download CSV", id="dl-csv", color="success"),
                    dbc.Button("Download JSON", id="dl-json", color="info"),
                ]
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Dash app setup

server = Flask(__name__)
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "MVP Data Enhance"
callbacks = TrulyUnifiedCallbacks(app)

app.layout = dbc.Container(
    [
        dcc.Store(id="session-store"),
        html.H2("MVP Data Enhancement Tool", className="text-center my-3"),
        dbc.Progress(id="progress", value=0, max=5, striped=True, animated=True),
        html.Div(id="main"),
        html.Div(id="alert"),
        dcc.Download(id="download"),
    ],
    fluid=True,
)

# ---------------------------------------------------------------------------
# Callback handlers


@callbacks.callback(
    [
        Output("main", "children"),
        Output("progress", "value"),
        Output("session-store", "data"),
        Output("alert", "children"),
        Output("download", "data"),
    ],
    [
        Input("upload-data", "contents"),
        Input("to-mapping", "n_clicks"),
        Input("to-device", "n_clicks"),
        Input("to-enhance", "n_clicks"),
        Input("dl-csv", "n_clicks"),
        Input("dl-json", "n_clicks"),
        Input({"type": "map-col", "index": ALL}, "value"),
        Input({"type": "dev-floor", "index": ALL}, "value"),
        Input({"type": "dev-sec", "index": ALL}, "value"),
        Input({"type": "dev-access", "index": ALL}, "value"),
        Input({"type": "dev-spec", "index": ALL}, "value"),
    ],
    [
        State("upload-data", "filename"),
        State("session-store", "data"),
        State({"type": "map-col", "index": ALL}, "id"),
        State({"type": "dev-floor", "index": ALL}, "id"),
    ],
    prevent_initial_call=True,
    callback_id="main_callback",
    component_name="mvp_data_enhance",
)
def main_callback(
    upload_contents,
    to_mapping,
    to_device,
    to_enhance,
    dl_csv,
    dl_json,
    map_values,
    dev_floor,
    dev_sec,
    dev_access,
    dev_spec,
    filename,
    store,
    map_ids,
    dev_ids,
):
    ctx = callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""
    SESSION.update(store or SESSION)
    download = None
    alert = None

    if trigger == "upload-data" and upload_contents:
        try:
            df = parse_contents(upload_contents, filename)
            SESSION.update(
                {
                    "raw_df": df.to_dict("records"),
                    "filename": filename,
                    "stage": "preview",
                }
            )
            return (
                layout_preview(df),
                1,
                SESSION,
                dbc.Alert("File loaded", color="success"),
                None,
            )
        except Exception as exc:  # pragma: no cover - runtime errors
            return (
                layout_upload(),
                0,
                SESSION,
                dbc.Alert(str(exc), color="danger"),
                None,
            )

    if SESSION.get("stage") == "preview" and trigger == "to-mapping":
        df = pd.DataFrame(SESSION["raw_df"])
        SESSION["stage"] = "mapping"
        return layout_column_mapping(df), 2, SESSION, None, None

    if SESSION.get("stage") == "mapping" and trigger == "to-device":
        mapping = {}
        for val, ident in zip(map_values, map_ids):
            if val:
                mapping[ident["index"]] = val
        SESSION["column_mapping"] = mapping
        df = pd.DataFrame(SESSION["raw_df"])
        SESSION["stage"] = "device"
        return layout_device_mapping(df), 3, SESSION, None, None

    if SESSION.get("stage") == "device" and trigger == "to-enhance":
        devices = []
        for i, ident in enumerate(dev_ids):
            door = ident["index"]
            devices.append(
                {
                    "door_id": door,
                    "floor_number": (
                        dev_floor[i] if dev_floor and i < len(dev_floor) else 1
                    ),
                    "security_level": dev_sec[i] if dev_sec and i < len(dev_sec) else 5,
                    "is_entry": "entry"
                    in (dev_access[i] if dev_access and i < len(dev_access) else []),
                    "is_exit": "exit"
                    in (dev_access[i] if dev_access and i < len(dev_access) else []),
                    "is_elevator": "is_elevator"
                    in (dev_spec[i] if dev_spec and i < len(dev_spec) else []),
                    "is_stairwell": "is_stairwell"
                    in (dev_spec[i] if dev_spec and i < len(dev_spec) else []),
                    "is_fire_escape": "is_fire_escape"
                    in (dev_spec[i] if dev_spec and i < len(dev_spec) else []),
                    "is_restricted": "is_restricted"
                    in (dev_spec[i] if dev_spec and i < len(dev_spec) else []),
                }
            )
        SESSION["device_mapping"] = devices
        df = pd.DataFrame(SESSION["raw_df"])
        df = apply_column_mapping(df, SESSION["column_mapping"])
        df = apply_device_mapping(df, devices)
        SESSION.update({"enhanced_df": df.to_dict("records"), "stage": "enhanced"})
        return (
            layout_enhanced(df, list(pd.DataFrame(SESSION["raw_df"]).columns)),
            5,
            SESSION,
            None,
            None,
        )

    if SESSION.get("stage") == "enhanced":
        df = pd.DataFrame(SESSION["enhanced_df"])
        if trigger == "dl-csv":
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            fname = f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            download = dict(content=csv_bytes, filename=fname)
        elif trigger == "dl-json":
            json_str = df.to_json(orient="records")
            fname = f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            download = dict(content=json_str, filename=fname)
        if download:
            return no_update, 5, SESSION, None, download

    stage = SESSION.get("stage")
    if stage == "upload":
        return layout_upload(), 0, SESSION, alert, download
    if stage == "preview":
        df = pd.DataFrame(SESSION["raw_df"])
        return layout_preview(df), 1, SESSION, alert, download
    if stage == "mapping":
        df = pd.DataFrame(SESSION["raw_df"])
        return layout_column_mapping(df), 2, SESSION, alert, download
    if stage == "device":
        df = pd.DataFrame(SESSION["raw_df"])
        return layout_device_mapping(df), 3, SESSION, alert, download
    if stage == "enhanced":
        df = pd.DataFrame(SESSION["enhanced_df"])
        return (
            layout_enhanced(df, list(pd.DataFrame(SESSION["raw_df"]).columns)),
            5,
            SESSION,
            alert,
            download,
        )
    return layout_upload(), 0, SESSION, alert, download


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=5003, debug=False)
