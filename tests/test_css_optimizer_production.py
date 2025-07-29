from yosai_intel_dashboard.models.css_build_optimizer import CSSOptimizer


def test_build_production_css_bundle(tmp_path):
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    output_dir = tmp_path / "out"

    # create imported css files
    (css_dir / "_a.css").write_text(".a { color: red; }\n")
    (css_dir / "_b.css").write_text(".b { margin: 0; }\n")

    # main.css with imports
    main_content = "@import './_a.css';\n@import \"./_b.css\";\n"
    (css_dir / "main.css").write_text(main_content)

    optimizer = CSSOptimizer(css_dir, output_dir)
    optimizer.build_production_css()

    out = output_dir / "main.min.css"
    gz = out.with_suffix(out.suffix + ".gz")
    assert out.exists()
    assert gz.exists()

    text = out.read_text()
    assert "@import" not in text
    assert ".a{color:red}" in text
    assert ".b{margin:0}" in text
