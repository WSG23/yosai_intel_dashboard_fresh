from models.css_build_optimizer import CSSOptimizer


def test_build_production_css_multifile(tmp_path):
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    output_dir = tmp_path / "out"

    # create multiple css files
    (css_dir / "main.css").write_text("body { color: red; }\n")
    (css_dir / "extra.css").write_text(".x { margin: 0; }\n")
    (css_dir / "theme.css").write_text("/* comment */\n.y{padding:5px;}\n")

    optimizer = CSSOptimizer(css_dir, output_dir)
    optimizer.build_production_css()

    for name in ["main", "extra", "theme"]:
        out = output_dir / f"{name}.min.css"
        gz = out.with_suffix(out.suffix + ".gz")
        assert out.exists()
        assert gz.exists()

