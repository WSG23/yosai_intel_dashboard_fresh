# models/css_build_optimizer.py - Type-safe CSS build and optimization
"""
Comprehensive CSS Quality Assurance & Performance Testing Suite
for Yōsai Intel Dashboard with strict type safety
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)

logger = logging.getLogger(__name__)

# Configure CSS utils logging with proper error handling
try:
    import cssutils

    # cssutils expects string level, not integer constant
    try:
        cssutils.log.setLevel("ERROR")  # Use string instead of logging.ERROR constant
    except AttributeError:  # pragma: no cover - handle unexpected api
        pass
except ImportError:
    logger.info("Warning: cssutils not available - some CSS analysis features disabled")
    cssutils = None


class CSSOptimizerError(Exception):
    """Base exception for CSS optimizer related errors."""


class PathValidationError(CSSOptimizerError):
    """Raised when provided file system paths are invalid."""


def validate_css_directory(path: Union[str, Path]) -> Path:
    """Return a valid CSS directory as ``Path``.

    Args:
        path: Directory path as ``str`` or ``Path``.

    Raises:
        PathValidationError: If the directory does not exist or is not a directory.

    """
    css_dir = Path(path)
    if not css_dir.exists() or not css_dir.is_dir():
        raise PathValidationError(f"CSS directory not found: {css_dir}")
    return css_dir


def ensure_output_directory(output_path: Union[str, Path]) -> Path:
    """Ensure the parent directory for ``output_path`` exists and return ``Path``."""
    output = Path(output_path)
    if output.parent and not output.parent.exists():
        output.parent.mkdir(parents=True, exist_ok=True)
    return output


def safe_path_conversion(path: Union[str, Path]) -> str:
    """Safely convert path to ``str`` representation with Unicode handling."""
    try:
        # Encode using surrogateescape to preserve any undecodable bytes and then
        # decode back to a normal UTF-8 string. This mirrors how Python's
        # filesystem encoding handles arbitrary bytes on POSIX systems.
        return (
            str(path)
            .encode("utf-8", errors="surrogateescape")
            .decode("utf-8", errors="replace")
        )
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.warning(f"Unicode conversion error for path {path}: {e}")
        return str(path).encode("ascii", errors="replace").decode("ascii")
    except Exception as exc:  # pragma: no cover - defensive
        raise PathValidationError(f"Invalid path: {path}") from exc


@dataclass
class CSSMetric:
    """CSS performance and quality metric"""

    name: str
    value: float
    unit: str
    status: str
    threshold: float
    description: str


@dataclass
class ComponentTest:
    """Component isolation test result"""

    component: str
    passes: List[str]
    failures: List[str]
    warnings: List[str]
    score: float


class CSSQualityAnalyzer:
    """Analyzes CSS for quality, performance, and best practices"""

    def __init__(self, css_dir: Path):
        self.css_dir = css_dir
        self.metrics: List[CSSMetric] = []
        self.violations: List[str] = []
        self.components: List[str] = []

    def analyze_bundle_size(self) -> CSSMetric:
        """Analyze CSS bundle size and compression"""
        main_css = self.css_dir / "main.css"

        if not main_css.exists():
            return CSSMetric(
                "bundle_size",
                0,
                "KB",
                "error",
                dynamic_config.css.bundle_threshold_kb,
                "Main CSS file not found",
            )

        # Calculate total size including imports
        total_size = 0
        processed_files = set()

        def calculate_size(css_file: Path) -> None:
            nonlocal total_size

            if css_file in processed_files:
                return
            processed_files.add(css_file)

            if css_file.exists():
                try:
                    content = css_file.read_text(encoding="utf-8")
                    total_size += len(content.encode("utf-8"))

                    # Find @import statements
                    imports = re.findall(r"@import\s+['\"]([^'\"]+)['\"]", content)
                    for import_path in imports:
                        import_file = css_file.parent / import_path
                        if import_file.exists():
                            calculate_size(import_file)
                except Exception as e:
                    logging.warning(f"Error reading CSS file {css_file}: {e}")

        calculate_size(main_css)
        size_kb = total_size / 1024

        # Determine status
        match size_kb:
            case _ if size_kb <= dynamic_config.css.bundle_excellent_kb:
                status = "excellent"
            case _ if size_kb <= dynamic_config.css.bundle_good_kb:
                status = "good"
            case _ if size_kb <= dynamic_config.css.bundle_warning_kb:

                status = "warning"
            case _:
                status = "critical"

        return CSSMetric(
            "bundle_size",
            round(size_kb, 2),
            "KB",
            status,
            dynamic_config.css.bundle_threshold_kb,
            "Total CSS bundle size including all imports",
        )

    def analyze_design_token_usage(self) -> CSSMetric:
        """Analyze design token usage vs hardcoded values"""
        hardcoded_patterns = [
            r"color:\s*#[0-9a-fA-F]{6}",
            r"background:\s*#[0-9a-fA-F]{6}",
            r"border-color:\s*#[0-9a-fA-F]{6}",
            r"padding:\s*\d+px",
            r"margin:\s*\d+px",
            r"border-radius:\s*\d+px",
            r"font-size:\s*\d+px",
        ]

        total_values = 0
        hardcoded_values = 0

        for css_file in self.css_dir.rglob("*.css"):
            if css_file.name.startswith("_") or css_file.name == "main.css":
                continue

            try:
                content = css_file.read_text(encoding="utf-8")

                for pattern in hardcoded_patterns:
                    matches = re.findall(pattern, content)
                    hardcoded_values += len(matches)

                # Count var() usage
                var_usage = len(re.findall(r"var\(--[^)]+\)", content))
                total_values += var_usage + hardcoded_values
            except Exception as e:
                logging.warning(f"Error analyzing file {css_file}: {e}")

        if total_values > 0:
            token_usage_percent = (
                (total_values - hardcoded_values) / total_values
            ) * 100
        else:
            token_usage_percent = 100

        match token_usage_percent:
            case _ if token_usage_percent >= 95:
                status = "excellent"
            case _ if token_usage_percent >= 85:
                status = "good"
            case _ if token_usage_percent >= 70:

                status = "warning"
            case _:
                status = "critical"

        return CSSMetric(
            "design_token_usage",
            round(token_usage_percent, 1),
            "%",
            status,
            90,
            "Percentage of values using design tokens vs hardcoded values",
        )

    def analyze_selector_specificity(self) -> CSSMetric:
        """Analyze CSS selector specificity for maintainability"""
        high_specificity_selectors = []
        total_selectors = 0

        for css_file in self.css_dir.rglob("*.css"):
            try:
                content = css_file.read_text(encoding="utf-8")

                # Parse CSS only if cssutils is available
                if cssutils:
                    try:
                        sheet = cssutils.parseString(content)
                        for rule in sheet:
                            if rule.type == rule.STYLE_RULE:
                                total_selectors += 1
                                selector_text = rule.selectorText

                                # Calculate specificity (simplified)
                                id_count = selector_text.count("#")
                                class_count = selector_text.count(".")
                                element_count = len(
                                    re.findall(r"\b[a-z]+\b", selector_text.lower())
                                )

                                specificity = (
                                    (id_count * 100)
                                    + (class_count * 10)
                                    + element_count
                                )

                                if (
                                    specificity > dynamic_config.css.specificity_high
                                ):  # High specificity threshold
                                    high_specificity_selectors.append(
                                        (selector_text, specificity)
                                    )
                    except Exception as e:
                        logging.warning(f"Error parsing CSS in {css_file}: {e}")
                else:
                    # Fallback simple analysis
                    selectors = re.findall(r"([^{}]+)\s*{", content)
                    total_selectors += len(selectors)

            except Exception as e:
                logging.warning(f"Error reading CSS file {css_file}: {e}")

        if total_selectors > 0:
            high_specificity_percent = (
                len(high_specificity_selectors) / total_selectors
            ) * 100
        else:
            high_specificity_percent = 0

        match high_specificity_percent:
            case _ if high_specificity_percent <= 5:
                status = "excellent"
            case _ if high_specificity_percent <= 10:
                status = "good"
            case _ if high_specificity_percent <= 20:

                status = "warning"
            case _:
                status = "critical"

        return CSSMetric(
            "selector_specificity",
            round(100 - high_specificity_percent, 1),
            "%",
            status,
            90,
            "Percentage of selectors with healthy specificity (< 30)",
        )

    def check_accessibility_compliance(self) -> CSSMetric:
        """Check CSS for accessibility compliance"""
        accessibility_score = 100
        violations = []

        for css_file in self.css_dir.rglob("*.css"):
            try:
                content = css_file.read_text(encoding="utf-8")

                # Check for focus styles
                if not re.search(r":focus", content) and "button" in content.lower():
                    violations.append(f"{css_file.name}: Missing focus styles")
                    accessibility_score -= 10

                # Check for proper contrast (simplified check)
                if re.search(r"color:\s*#(?:808080|888888|999999)", content):
                    violations.append(
                        f"{css_file.name}: Potentially low contrast colors"
                    )
                    accessibility_score -= 5

                # Check for reduced motion support
                if "@media" in content and "prefers-reduced-motion" not in content:
                    violations.append(f"{css_file.name}: No reduced motion support")
                    accessibility_score -= 5

            except Exception as e:
                logging.warning(f"Error checking accessibility in {css_file}: {e}")

        accessibility_score = max(0, accessibility_score)

        match accessibility_score:
            case _ if accessibility_score >= 95:
                status = "excellent"
            case _ if accessibility_score >= 85:
                status = "good"
            case _ if accessibility_score >= 70:

                status = "warning"
            case _:
                status = "critical"

        return CSSMetric(
            "accessibility_compliance",
            accessibility_score,
            "%",
            status,
            90,
            "CSS accessibility compliance score",
        )

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete CSS quality analysis"""
        logger.info("🔍 Running comprehensive CSS quality analysis...")

        # Run all metric analyses
        metrics = [
            self.analyze_bundle_size(),
            self.analyze_design_token_usage(),
            self.analyze_selector_specificity(),
            self.check_accessibility_compliance(),
        ]

        # Calculate overall score
        metric_scores = [m.value for m in metrics if m.status != "error"]
        overall_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0

        return {
            "overall_score": round(overall_score, 1),
            "metrics": metrics,
            "timestamp": time.time(),
        }


class CSSOptimizer:
    """Optimizes CSS for production deployment"""

    def __init__(self, css_dir: Path, output_dir: Path):
        self.css_dir = css_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def minify_css(self, input_file: Path, output_file: Path) -> None:
        """Minify CSS file"""
        try:
            content = input_file.read_text(encoding="utf-8")

            # Remove comments
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            # Remove whitespace
            content = re.sub(r"\s+", " ", content)
            content = re.sub(r";\s*}", "}", content)
            content = re.sub(r"{\s*", "{", content)
            content = re.sub(r"}\s*", "}", content)
            content = re.sub(r":\s*", ":", content)
            content = re.sub(r";\s*", ";", content)

            # Remove unnecessary semicolons
            content = re.sub(r";}", "}", content)

            output_file.write_text(content.strip(), encoding="utf-8")

            # Calculate compression
            original_size = len(input_file.read_text(encoding="utf-8"))
            minified_size = len(content)
            compression_ratio = (1 - minified_size / original_size) * 100

            logger.info(
                f"✅ Minified {input_file.name}: {compression_ratio:.1f}% smaller"
            )

        except Exception as e:
            logger.info(f"❌ Error minifying {input_file}: {e}")

    def build_production_css(self) -> None:
        """Bundle, minify and compress main CSS file for production."""
        logger.info("🏗️ Building production CSS...")

        try:
            main_css = self.css_dir / "main.css"
            if not main_css.exists():
                logger.info("❌ main.css not found")
                return

            imports: List[str] = []
            remaining_lines: List[str] = []

            for line in main_css.read_text(encoding="utf-8").splitlines(True):
                m = re.match(r"\s*@import\s+[\'\"]([^\'\"]+)[\'\"]", line)
                if m:
                    imports.append(m.group(1))
                else:
                    remaining_lines.append(line)

            segments: List[str] = []
            segments.append("".join(remaining_lines))
            for rel in imports:
                try:
                    path = main_css.parent / rel
                    segments.append(path.read_text(encoding="utf-8"))
                except Exception as exc:
                    logger.error(f"❌ Error reading {path}: {exc}")
            bundle = "".join(segments)

            out = self.output_dir / "main.min.css"
            tmp = out.with_suffix(".tmp.css")
            tmp.write_text(bundle, encoding="utf-8")

            self.minify_css(tmp, out)
            tmp.unlink(missing_ok=True)

            import gzip

            with open(out, "rb") as f_in:
                with gzip.open(f"{out}.gz", "wb") as f_out:
                    f_out.write(f_in.read())

            try:
                import brotli  # type: ignore

                with open(out, "rb") as f_in:
                    compressed = brotli.compress(f_in.read())
                    with open(f"{out}.br", "wb") as f_out:
                        f_out.write(compressed)
                logger.info(f"✅ Brotli version: {out}.br")
            except Exception:
                logger.info("ℹ️ Brotli compression skipped")

            logger.info(f"✅ Production CSS created: {out}")
            logger.info(f"✅ Gzipped version: {out}.gz")

        except Exception as e:
            logger.info(f"❌ Error building production CSS: {e}")


def generate_css_report(
    css_dir: Path, output_file: Path | None = None
) -> Dict[str, Any]:
    """Generate comprehensive CSS quality report"""

    logger.info("📊 Generating comprehensive CSS quality report...")

    # Initialize analyzer
    quality_analyzer = CSSQualityAnalyzer(css_dir)

    # Run analysis
    quality_results = quality_analyzer.run_full_analysis()

    # Compile report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_score": quality_results["overall_score"],
        "quality_metrics": [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "status": m.status,
                "threshold": m.threshold,
                "description": m.description,
            }
            for m in quality_results["metrics"]
        ],
        "recommendations": _generate_recommendations(quality_results),
    }

    # Save report only when a path is provided
    if output_file is not None:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"📋 Report saved to: {output_file}")
        except Exception as e:
            logger.info(f"❌ Error saving report: {e}")

    return report


def _generate_recommendations(quality_results: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recommendations = []

    metrics = quality_results.get("metrics", [])

    for metric in metrics:
        if metric.status == "critical":
            if metric.name == "bundle_size":
                recommendations.append(
                    "Consider splitting CSS into critical and non-critical parts"
                )
            elif metric.name == "design_token_usage":
                recommendations.append("Replace hardcoded values with design tokens")
            elif metric.name == "accessibility_compliance":
                recommendations.append(
                    "Add missing accessibility features (focus styles, reduced motion)"
                )

    if not recommendations:
        recommendations.append(
            "Great job! Your CSS architecture meets all quality standards."
        )

    return recommendations


def print_report_summary(report: Dict[str, Any]) -> None:
    """Print a formatted summary of the CSS quality report"""

    logger.info("\n" + "=" * 60)
    logger.info("🎯 CSS QUALITY REPORT SUMMARY")
    logger.info("=" * 60)

    logger.info(f"\n📊 OVERALL SCORE: {report['overall_score']:.1f}/100")

    # Status indicator
    score = report["overall_score"]
    if score >= 90:
        logger.info("🟢 EXCELLENT - World-class CSS architecture!")
    elif score >= 80:
        logger.info("🟡 GOOD - Minor improvements needed")
    elif score >= 70:
        logger.info("🟠 WARNING - Several issues to address")
    else:
        logger.info("🔴 CRITICAL - Major refactoring needed")

    logger.info(f"\n📅 Generated: {report['timestamp']}")

    logger.info("\n📏 QUALITY METRICS:")
    for metric in report["quality_metrics"]:
        status_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "warning": "🟠",
            "critical": "🔴",
            "error": "❌",
        }.get(metric["status"], "⚪")

        logger.info(
            f"  {status_emoji} "
            f"{metric['name'].replace('_', ' ').title()}: "
            f"{metric['value']}{metric['unit']}"
        )

    logger.info("\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(report["recommendations"], 1):
        logger.info(f"  {i}. {rec}")

    logger.info("\n" + "=" * 60)


def generate_css_report_safe(
    css_directory: Union[str, Path], output_file: Union[str, Path]
) -> Dict[str, Any]:
    """Wrapper around :func:`generate_css_report` with path validation."""

    css_dir = validate_css_directory(css_directory)
    out_file = ensure_output_directory(output_file)
    return generate_css_report(
        Path(safe_path_conversion(css_dir)), Path(safe_path_conversion(out_file))
    )


if __name__ == "__main__":
    import sys

    css_arg = sys.argv[1] if len(sys.argv) > 1 else "assets/css"

    try:
        css_dir = validate_css_directory(css_arg)
        report_file = ensure_output_directory(
            Path(css_dir).parent / "css-quality-report.json"
        )
        report = generate_css_report_safe(css_dir, report_file)
    except PathValidationError as exc:
        logger.info(f"❌ {exc}")
        logger.info("Usage: python css_build_optimizer.py [css_directory]")
        sys.exit(1)

    print_report_summary(report)

    logger.info(f"\n📋 Full report available at: {report_file}")
    logger.info("\n🚀 Next steps:")
    logger.info("1. Review recommendations and address critical issues")
    logger.info("2. Run performance tests on live application")
    logger.info("3. Set up automated quality monitoring")

# Export main functions
__all__ = [
    "CSSQualityAnalyzer",
    "CSSOptimizer",
    "generate_css_report",
    "print_report_summary",
    "validate_css_directory",
    "ensure_output_directory",
    "safe_path_conversion",
    "generate_css_report_safe",
]
