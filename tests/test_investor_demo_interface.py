import io
import sys
import types
import pandas as pd
import pytest

# Provide minimal stubs for external modules used by investor_demo_interface
sys.modules.setdefault('mvp_cli_engine', types.SimpleNamespace(
    load_dataframe=lambda p: pd.DataFrame(),
    generate_analytics=lambda df: {}
))
sys.modules.setdefault('simple_mapping_interface', types.SimpleNamespace(
    enhance_data_with_mappings=lambda df, c, d: (df, {})
))
sys.modules.setdefault('unicode_fix_module', types.SimpleNamespace(
    safe_file_write=lambda p, d: None
))

import investor_demo_interface as demo


def setup_function():
    demo.current_df = None
    demo.column_mapping = {}
    demo.device_mapping = []


@pytest.fixture
def client():
    demo.app.config['TESTING'] = True
    with demo.app.test_client() as c:
        yield c


def test_build_stages():
    stages = demo.build_stages(2)
    assert stages[0]['complete'] is True
    assert stages[1]['complete'] is False
    assert stages[2]['complete'] is False


def test_upload_sets_dataframe(monkeypatch, client):
    df = pd.DataFrame({'A': [1]})
    monkeypatch.setattr(demo, 'load_dataframe', lambda path: df)
    data = {'file': (io.BytesIO(b'A\n1\n'), 'test.csv')}
    resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 302
    assert demo.current_df is df


def test_results_generates_file(monkeypatch, client):
    demo.current_df = pd.DataFrame({'A': [1]})
    monkeypatch.setattr(demo, 'enhance_data_with_mappings', lambda df, c, d: (df, {}))
    monkeypatch.setattr(demo, 'generate_analytics', lambda df: {'rows': len(df)})
    monkeypatch.setattr(demo, 'safe_file_write', lambda p, d: None)
    resp = client.get('/results')
    assert resp.status_code == 200

