from api.cache import cached_json_response


def test_cached_json_response_sets_headers():
    resp = cached_json_response({"foo": "bar"}, max_age=1)
    assert resp.headers.get("Cache-Control") == "public, max-age=1"
    assert "ETag" in resp.headers
    assert "Expires" in resp.headers
