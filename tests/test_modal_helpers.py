import dash_bootstrap_components as dbc
from dash.dash import no_update

from pages.file_upload import open_modals, save_column_mappings, close_modals


def test_open_modals_verify():
    result = open_modals("verify-columns-btn-simple.n_clicks", 1, None)
    assert result == (no_update, True, no_update)


def test_open_modals_classify():
    result = open_modals("classify-devices-btn.n_clicks", None, 1)
    assert result == (no_update, no_update, True)


def test_save_column_mappings():
    toast, col, dev = save_column_mappings("column-verify-confirm.n_clicks", 1)
    assert isinstance(toast, dbc.Toast)
    assert col is False
    assert dev is no_update


def test_close_modals():
    result = close_modals("column-verify-cancel.n_clicks")
    assert result == (no_update, False, False)
