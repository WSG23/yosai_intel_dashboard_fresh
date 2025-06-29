import pages.file_upload as fu


def test_open_modals_verify():
    result = fu.open_modals("verify-columns-btn-simple.n_clicks", 1, None)
    assert result == (fu.no_update, True, fu.no_update)


def test_open_modals_classify():
    result = fu.open_modals("classify-devices-btn.n_clicks", 0, 1)
    assert result == (fu.no_update, fu.no_update, True)


def test_save_column_mappings():
    res = fu.save_column_mappings("column-verify-confirm.n_clicks", 1)
    assert isinstance(res[0], fu.dbc.Toast)
    assert res[1:] == (False, fu.no_update)


def test_close_modals():
    res = fu.close_modals("device-verify-cancel.n_clicks", None, 1)
    assert res == (fu.no_update, False, False)

