from pathlib import Path


def GenerateIntegrationGuide() -> str:
    """Return the compliance integration guide markdown text."""
    guide_path = (
        Path(__file__).resolve().parent.parent
        / "plugins"
        / "compliance_plugin"
        / "COMPLETE COMPLIANCE FRAMEWORK INTEGRATION GUIDE"
    )
    try:
        text = guide_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Guide file not found: {guide_path}")
    return text.strip()
