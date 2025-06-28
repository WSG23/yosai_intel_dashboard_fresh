# models/css_build_optimizer.py - FIXED: Type-safe CSS build and optimization
"""
Comprehensive CSS Quality Assurance & Performance Testing Suite
for Yōsai Intel Dashboard - FIXED version with proper type safety
"""

import os
import re
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from config.dynamic_config import dynamic_config
import logging

# FIXED: Configure CSS utils logging with proper error handling
try:
    import cssutils
    # FIXED: cssutils expects string level, not integer constant
    cssutils.log.setLevel('ERROR')  # Use string instead of logging.ERROR constant
except ImportError:
    print("Warning: cssutils not available - some CSS analysis features disabled")
    cssutils = None

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
            return CSSMetric("bundle_size", 0, "KB", "error", dynamic_config.css.bundle_threshold_kb, "Main CSS file not found")
        
        # Calculate total size including imports
        total_size = 0
        processed_files = set()
        
        def calculate_size(css_file: Path) -> None:
            nonlocal total_size, processed_files
            
            if css_file in processed_files:
                return
            processed_files.add(css_file)
            
            if css_file.exists():
                try:
                    content = css_file.read_text(encoding='utf-8')
                    total_size += len(content.encode('utf-8'))
                    
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
        if size_kb <= dynamic_config.css.bundle_excellent_kb:
            status = "excellent"
        elif size_kb <= dynamic_config.css.bundle_good_kb:
            status = "good"
        elif size_kb <= dynamic_config.css.bundle_warning_kb:
            status = "warning"
        else:
            status = "critical"
        
        return CSSMetric(
            "bundle_size", 
            round(size_kb, 2), 
            "KB", 
            status, 
            dynamic_config.css.bundle_threshold_kb, 
            f"Total CSS bundle size including all imports"
        )
    
    def analyze_design_token_usage(self) -> CSSMetric:
        """Analyze design token usage vs hardcoded values"""
        hardcoded_patterns = [
            r'color:\s*#[0-9a-fA-F]{6}',
            r'background:\s*#[0-9a-fA-F]{6}',
            r'border-color:\s*#[0-9a-fA-F]{6}',
            r'padding:\s*\d+px',
            r'margin:\s*\d+px',
            r'border-radius:\s*\d+px',
            r'font-size:\s*\d+px'
        ]
        
        total_values = 0
        hardcoded_values = 0
        
        for css_file in self.css_dir.rglob("*.css"):
            if css_file.name.startswith('_') or css_file.name == 'main.css':
                continue
                
            try:
                content = css_file.read_text(encoding='utf-8')
                
                for pattern in hardcoded_patterns:
                    matches = re.findall(pattern, content)
                    hardcoded_values += len(matches)
                
                # Count var() usage
                var_usage = len(re.findall(r'var\(--[^)]+\)', content))
                total_values += var_usage + hardcoded_values
            except Exception as e:
                logging.warning(f"Error analyzing file {css_file}: {e}")
        
        if total_values > 0:
            token_usage_percent = ((total_values - hardcoded_values) / total_values) * 100
        else:
            token_usage_percent = 100
        
        if token_usage_percent >= 95:
            status = "excellent"
        elif token_usage_percent >= 85:
            status = "good"
        elif token_usage_percent >= 70:
            status = "warning"
        else:
            status = "critical"
        
        return CSSMetric(
            "design_token_usage",
            round(token_usage_percent, 1),
            "%",
            status,
            90,
            f"Percentage of values using design tokens vs hardcoded values"
        )
    
    def analyze_selector_specificity(self) -> CSSMetric:
        """Analyze CSS selector specificity for maintainability"""
        high_specificity_selectors = []
        total_selectors = 0
        
        for css_file in self.css_dir.rglob("*.css"):
            try:
                content = css_file.read_text(encoding='utf-8')
                
                # Parse CSS only if cssutils is available
                if cssutils:
                    try:
                        sheet = cssutils.parseString(content)
                        for rule in sheet:
                            if rule.type == rule.STYLE_RULE:
                                total_selectors += 1
                                selector_text = rule.selectorText
                                
                                # Calculate specificity (simplified)
                                id_count = selector_text.count('#')
                                class_count = selector_text.count('.')
                                element_count = len(re.findall(r'\b[a-z]+\b', selector_text.lower()))
                                
                                specificity = (id_count * 100) + (class_count * 10) + element_count
                                
                                if specificity > dynamic_config.css.specificity_high:  # High specificity threshold
                                    high_specificity_selectors.append((selector_text, specificity))
                    except Exception as e:
                        logging.warning(f"Error parsing CSS in {css_file}: {e}")
                else:
                    # Fallback simple analysis
                    selectors = re.findall(r'([^{}]+)\s*{', content)
                    total_selectors += len(selectors)
                    
            except Exception as e:
                logging.warning(f"Error reading CSS file {css_file}: {e}")
        
        if total_selectors > 0:
            high_specificity_percent = (len(high_specificity_selectors) / total_selectors) * 100
        else:
            high_specificity_percent = 0
        
        if high_specificity_percent <= 5:
            status = "excellent"
        elif high_specificity_percent <= 10:
            status = "good"
        elif high_specificity_percent <= 20:
            status = "warning"
        else:
            status = "critical"
        
        return CSSMetric(
            "selector_specificity",
            round(100 - high_specificity_percent, 1),
            "%",
            status,
            90,
            f"Percentage of selectors with healthy specificity (< 30)"
        )
    
    def check_accessibility_compliance(self) -> CSSMetric:
        """Check CSS for accessibility compliance"""
        accessibility_score = 100
        violations = []
        
        for css_file in self.css_dir.rglob("*.css"):
            try:
                content = css_file.read_text(encoding='utf-8')
                
                # Check for focus styles
                if not re.search(r':focus', content) and 'button' in content.lower():
                    violations.append(f"{css_file.name}: Missing focus styles")
                    accessibility_score -= 10
                
                # Check for proper contrast (simplified check)
                if re.search(r'color:\s*#(?:808080|888888|999999)', content):
                    violations.append(f"{css_file.name}: Potentially low contrast colors")
                    accessibility_score -= 5
                
                # Check for reduced motion support
                if '@media' in content and 'prefers-reduced-motion' not in content:
                    violations.append(f"{css_file.name}: No reduced motion support")
                    accessibility_score -= 5
                    
            except Exception as e:
                logging.warning(f"Error checking accessibility in {css_file}: {e}")
        
        accessibility_score = max(0, accessibility_score)
        
        if accessibility_score >= 95:
            status = "excellent"
        elif accessibility_score >= 85:
            status = "good"
        elif accessibility_score >= 70:
            status = "warning"
        else:
            status = "critical"
        
        return CSSMetric(
            "accessibility_compliance",
            accessibility_score,
            "%",
            status,
            90,
            f"CSS accessibility compliance score"
        )
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete CSS quality analysis"""
        print("🔍 Running comprehensive CSS quality analysis...")
        
        # Run all metric analyses
        metrics = [
            self.analyze_bundle_size(),
            self.analyze_design_token_usage(),
            self.analyze_selector_specificity(),
            self.check_accessibility_compliance()
        ]
        
        # Calculate overall score
        metric_scores = [m.value for m in metrics if m.status != "error"]
        overall_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0
        
        return {
            "overall_score": round(overall_score, 1),
            "metrics": metrics,
            "timestamp": time.time()
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
            content = input_file.read_text(encoding='utf-8')
            
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # Remove whitespace
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', '}', content)
            content = re.sub(r'{\s*', '{', content)
            content = re.sub(r'}\s*', '}', content)
            content = re.sub(r':\s*', ':', content)
            content = re.sub(r';\s*', ';', content)
            
            # Remove unnecessary semicolons
            content = re.sub(r';}', '}', content)
            
            output_file.write_text(content.strip(), encoding='utf-8')
            
            # Calculate compression
            original_size = len(input_file.read_text(encoding='utf-8'))
            minified_size = len(content)
            compression_ratio = (1 - minified_size / original_size) * 100
            
            print(f"✅ Minified {input_file.name}: {compression_ratio:.1f}% smaller")
            
        except Exception as e:
            print(f"❌ Error minifying {input_file}: {e}")
    
    def build_production_css(self) -> None:
        """Build optimized CSS for production"""
        print("🏗️ Building production CSS...")
        
        try:
            # Create main production CSS
            main_css = self.css_dir / "main.css"
            if main_css.exists():
                prod_main = self.output_dir / "main.min.css"
                self.minify_css(main_css, prod_main)
                
                # Create gzipped version
                import gzip
                with open(prod_main, 'rb') as f_in:
                    with gzip.open(f"{prod_main}.gz", 'wb') as f_out:
                        f_out.write(f_in.read())
                
                print(f"✅ Production CSS created: {prod_main}")
                print(f"✅ Gzipped version: {prod_main}.gz")
            else:
                print("❌ Main CSS file not found")
                
        except Exception as e:
            print(f"❌ Error building production CSS: {e}")

def generate_css_report(css_dir: Path, output_file: Optional[Path] = None) -> Dict[str, Any]:  # FIXED: Optional[Path] instead of Path
    """Generate comprehensive CSS quality report"""
    
    print("📊 Generating comprehensive CSS quality report...")
    
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
                "description": m.description
            } for m in quality_results["metrics"]
        ],
        "recommendations": _generate_recommendations(quality_results)
    }
    
    # FIXED: Save report with proper null checking
    if output_file is not None:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"📋 Report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    return report

def _generate_recommendations(quality_results: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recommendations = []
    
    metrics = quality_results.get("metrics", [])
    
    for metric in metrics:
        if metric.status == "critical":
            if metric.name == "bundle_size":
                recommendations.append("Consider splitting CSS into critical and non-critical parts")
            elif metric.name == "design_token_usage":
                recommendations.append("Replace hardcoded values with design tokens")
            elif metric.name == "accessibility_compliance":
                recommendations.append("Add missing accessibility features (focus styles, reduced motion)")
    
    if not recommendations:
        recommendations.append("Great job! Your CSS architecture meets all quality standards.")
    
    return recommendations

def print_report_summary(report: Dict[str, Any]) -> None:
    """Print a formatted summary of the CSS quality report"""
    
    print("\n" + "=" * 60)
    print("🎯 CSS QUALITY REPORT SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 OVERALL SCORE: {report['overall_score']:.1f}/100")
    
    # Status indicator
    score = report['overall_score']
    if score >= 90:
        print("🟢 EXCELLENT - World-class CSS architecture!")
    elif score >= 80:
        print("🟡 GOOD - Minor improvements needed")
    elif score >= 70:
        print("🟠 WARNING - Several issues to address")
    else:
        print("🔴 CRITICAL - Major refactoring needed")
    
    print(f"\n📅 Generated: {report['timestamp']}")
    
    print(f"\n📏 QUALITY METRICS:")
    for metric in report['quality_metrics']:
        status_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "warning": "🟠",
            "critical": "🔴",
            "error": "❌"
        }.get(metric['status'], "⚪")
        
        print(f"  {status_emoji} {metric['name'].replace('_', ' ').title()}: {metric['value']}{metric['unit']}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    import sys
    
    # Get CSS directory from command line or use default
    if len(sys.argv) > 1:
        css_dir = Path(sys.argv[1])
    else:
        css_dir = Path("assets/css")
    
    if not css_dir.exists():
        print(f"❌ CSS directory not found: {css_dir}")
        print("Usage: python css_build_optimizer.py [css_directory]")
        sys.exit(1)
    
    # Generate report
    report_file = css_dir.parent / "css-quality-report.json"
    report = generate_css_report(css_dir, report_file)  # FIXED: Pass Path object properly
    
    # Print summary
    print_report_summary(report)
    
    print(f"\n📋 Full report available at: {report_file}")
    print("\n🚀 Next steps:")
    print("1. Review recommendations and address critical issues")
    print("2. Run performance tests on live application")
    print("3. Set up automated quality monitoring")

# Export main functions
__all__ = ['CSSQualityAnalyzer', 'CSSOptimizer', 'generate_css_report', 'print_report_summary']