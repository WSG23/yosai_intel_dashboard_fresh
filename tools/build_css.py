from pathlib import Path

from yosai_intel_dashboard.src.core.domain import css_build_optimizer

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# Alias to maintain naming from documentation
CSSBuildOptimizer = css_build_optimizer.CSSOptimizer


def main() -> None:
    css_dir = ASSETS_DIR / "css"
    output_dir = ASSETS_DIR / "dist"
    optimizer = CSSBuildOptimizer(css_dir, output_dir)
    optimizer.build_production_css()

    built = output_dir / "main.min.css"
    gzipped = output_dir / "main.min.css.gz"
    if not (built.exists() and gzipped.exists()):
        raise SystemExit("CSS build failed to produce expected artifacts")


if __name__ == "__main__":
    main()
