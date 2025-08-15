from models import load_model


def test_load_model_versions():
    model_v1 = load_model("1")
    model_v2 = load_model("2")

    assert model_v1(3) == 3  # factor 1.0
    assert model_v2(3) == 6  # factor 2.0
