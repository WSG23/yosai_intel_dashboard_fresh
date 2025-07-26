from analysis.unified_analyzer import UnifiedAnalyzer


def test_unified_analyzer_basic(tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("def foo():\n    pass\n")
    analyzer = UnifiedAnalyzer(tmp_path)
    results = analyzer.analyze()
    assert results["python"]["files_analyzed"] == 1
