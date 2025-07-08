#!/usr/bin/env python3
"""
Tailored Callback Pattern Auditor - Specific to your current system architecture
Identifies all callback patterns across TrulyUnifiedCallbacks, MasterCallbackSystem, 
CallbackRegistry, CallbackController, and legacy patterns.
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import json

@dataclass
class CallbackPattern:
    file_path: str
    line_number: int
    pattern_type: str
    decorator_name: str
    callback_id: Optional[str]
    component_name: Optional[str]
    raw_code: str
    output_targets: List[str]
    input_sources: List[str]
    function_name: str
    complexity_score: int

@dataclass
class ConflictAnalysis:
    output_id: str
    conflicting_files: List[str]
    conflicting_callbacks: List[str]
    severity: str
    resolution_suggestion: str

class YourSystemCallbackAuditor:
    """Auditor specifically designed for your callback architecture"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.patterns: List[CallbackPattern] = []
        self.conflicts: List[ConflictAnalysis] = []
        self.pattern_counts = Counter()
        self.namespace_usage = defaultdict(list)
        self.output_conflicts = defaultdict(list)
        
        # Define your specific callback patterns
        self.callback_signatures = {
            # TrulyUnifiedCallbacks patterns
            'truly_unified_callback': [
                r'@callbacks\.callback\(',
                r'@callbacks\.unified_callback\(',
                r'@callbacks\.register_callback\(',
            ],
            # MasterCallbackSystem patterns  
            'master_callback_system': [
                r'@system\.register_dash_callback\(',
                r'@master_system\.register_dash_callback\(',
            ],
            # CallbackRegistry patterns
            'callback_registry': [
                r'registry\.handle_register\(',
                r'\.handle_register\(',
            ],
            # CallbackController event patterns
            'callback_controller': [
                r'controller\.handle_register\(',
                r'CallbackController\(\)\.handle_register\(',
                r'\.handle_register\(CallbackEvent\.',
            ],
            # Legacy Dash patterns
            'legacy_dash': [
                r'@app\.callback\(',
                r'app\.callback\(',
            ],
            # Clientside callbacks
            'clientside_callback': [
                r'\.clientside_callback\(',
                r'app\.clientside_callback\(',
                r'\.handle_register_clientside\(',
            ]
        }
    
    def scan_complete_codebase(self) -> Dict[str, any]:
        """Comprehensive scan of your entire codebase"""
        print("🔍 Starting comprehensive callback pattern audit...")
        
        results = {
            'summary': {},
            'patterns_by_type': defaultdict(list),
            'conflicts': [],
            'recommendations': [],
            'file_analysis': {},
            'namespace_analysis': {},
            'unicode_risks': []
        }
        
        # Scan all Python files
        python_files = list(self.root_path.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            file_patterns = self._analyze_file_comprehensively(py_file)
            for pattern in file_patterns:
                self.patterns.append(pattern)
                self.pattern_counts[pattern.pattern_type] += 1
                results['patterns_by_type'][pattern.pattern_type].append(pattern)
                
                # Track namespace usage
                if pattern.component_name:
                    self.namespace_usage[pattern.component_name].append(pattern.callback_id)
                
                # Track potential output conflicts
                for output in pattern.output_targets:
                    self.output_conflicts[output].append({
                        'file': str(py_file),
                        'callback_id': pattern.callback_id,
                        'line': pattern.line_number
                    })
        
        # Analyze conflicts
        results['conflicts'] = self._analyze_output_conflicts()
        
        # Generate summary
        results['summary'] = self._generate_summary()
        
        # Namespace analysis
        results['namespace_analysis'] = self._analyze_namespaces()
        
        # Unicode risk assessment
        results['unicode_risks'] = self._assess_unicode_risks()
        
        # Generate recommendations
        results['recommendations'] = self._generate_consolidation_recommendations()
        
        print(f"✅ Audit complete! Found {len(self.patterns)} callbacks across {len(self.pattern_counts)} pattern types")
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Skip test files, migrations, and vendor code"""
        skip_patterns = [
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'migrations/', 'test_', 'tests/', '.pytest_cache',
            'build/', 'dist/', '.tox/'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file_comprehensively(self, file_path: Path) -> List[CallbackPattern]:
        """Deep analysis of a single Python file"""
        patterns = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST for decorator analysis
            try:
                tree = ast.parse(content)
                ast_patterns = self._extract_ast_patterns(tree, file_path, lines)
                patterns.extend(ast_patterns)
            except SyntaxError as e:
                print(f"⚠️  Syntax error in {file_path}: {e}")
            
            # Regex analysis for patterns that might be missed by AST
            regex_patterns = self._extract_regex_patterns(content, file_path, lines)
            patterns.extend(regex_patterns)
            
        except UnicodeDecodeError as e:
            print(f"⚠️  Unicode error reading {file_path}: {e}")
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
        
        return patterns
    
    def _extract_ast_patterns(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CallbackPattern]:
        """Extract callback patterns from AST analysis"""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    pattern = self._analyze_decorator(decorator, node, file_path, lines)
                    if pattern:
                        patterns.append(pattern)
        
        return patterns
    
    def _analyze_decorator(self, decorator: ast.AST, func_node: ast.FunctionDef, file_path: Path, lines: List[str]) -> Optional[CallbackPattern]:
        """Analyze individual decorator for callback patterns"""
        decorator_code = self._get_decorator_source(decorator, lines)
        
        # Match against your specific patterns
        pattern_type = self._classify_pattern_type(decorator_code)
        if not pattern_type:
            return None
        
        # Extract callback details
        callback_id = self._extract_callback_id_from_decorator(decorator)
        component_name = self._extract_component_name_from_decorator(decorator)
        output_targets = self._extract_outputs_from_decorator(decorator)
        input_sources = self._extract_inputs_from_decorator(decorator)
        
        # Calculate complexity score
        complexity = self._calculate_complexity_score(func_node, len(output_targets), len(input_sources))
        
        return CallbackPattern(
            file_path=str(file_path),
            line_number=getattr(decorator, 'lineno', 0),
            pattern_type=pattern_type,
            decorator_name=self._get_decorator_name(decorator),
            callback_id=callback_id,
            component_name=component_name,
            raw_code=decorator_code.strip(),
            output_targets=output_targets,
            input_sources=input_sources,
            function_name=func_node.name,
            complexity_score=complexity
        )
    
    def _classify_pattern_type(self, decorator_code: str) -> Optional[str]:
        """Classify the callback pattern type"""
        for pattern_type, signatures in self.callback_signatures.items():
            for signature in signatures:
                if re.search(signature, decorator_code):
                    return pattern_type
        return None
    
    def _extract_regex_patterns(self, content: str, file_path: Path, lines: List[str]) -> List[CallbackPattern]:
        """Extract patterns using regex for edge cases AST might miss"""
        patterns = []
        
        # Look for event handler registrations
        event_patterns = [
            r'\.handle_register\(CallbackEvent\.(\w+)',
            r'\.register\(CallbackEvent\.(\w+)',
            r'controller\.fire_event\(CallbackEvent\.(\w+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in event_patterns:
                if re.search(pattern, line):
                    patterns.append(CallbackPattern(
                        file_path=str(file_path),
                        line_number=i + 1,
                        pattern_type='callback_controller_event',
                        decorator_name='event_handler',
                        callback_id=None,
                        component_name=None,
                        raw_code=line.strip(),
                        output_targets=[],
                        input_sources=[],
                        function_name='unknown',
                        complexity_score=1
                    ))
        
        return patterns
    
    def _get_decorator_source(self, decorator: ast.AST, lines: List[str]) -> str:
        """Get source code for decorator"""
        lineno = getattr(decorator, 'lineno', None)
        if lineno is not None and lineno <= len(lines):
            # Try to get the full decorator which might span multiple lines
            start_line = lineno - 1
            end_line = start_line
            
            # Find the full decorator by looking for the opening and closing parentheses
            paren_count = 0
            in_decorator = False
            
            for i in range(start_line, min(len(lines), start_line + 10)):  # Look ahead max 10 lines
                line = lines[i]
                if '@' in line or in_decorator:
                    in_decorator = True
                    paren_count += line.count('(') - line.count(')')
                    end_line = i
                    if paren_count == 0 and '(' in line:
                        break
            
            return '\n'.join(lines[start_line:end_line + 1])
        
        return str(decorator)
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"
    
    def _extract_callback_id_from_decorator(self, decorator: ast.AST) -> Optional[str]:
        """Extract callback_id from decorator arguments"""
        if isinstance(decorator, ast.Call):
            for keyword in getattr(decorator, 'keywords', []):
                if keyword.arg == 'callback_id':
                    if isinstance(keyword.value, ast.Constant):
                        return keyword.value.value
                    elif isinstance(keyword.value, ast.Str):  # Python < 3.8
                        return keyword.value.s
        return None
    
    def _extract_component_name_from_decorator(self, decorator: ast.AST) -> Optional[str]:
        """Extract component_name from decorator arguments"""
        if isinstance(decorator, ast.Call):
            for keyword in getattr(decorator, 'keywords', []):
                if keyword.arg == 'component_name':
                    if isinstance(keyword.value, ast.Constant):
                        return keyword.value.value
                    elif isinstance(keyword.value, ast.Str):  # Python < 3.8
                        return keyword.value.s
        return None
    
    def _extract_outputs_from_decorator(self, decorator: ast.AST) -> List[str]:
        """Extract Output targets from decorator"""
        outputs = []
        if isinstance(decorator, ast.Call) and decorator.args:
            # First argument is typically Output(s)
            first_arg = decorator.args[0]
            outputs.extend(self._parse_dash_dependency(first_arg, 'Output'))
        return outputs
    
    def _extract_inputs_from_decorator(self, decorator: ast.AST) -> List[str]:
        """Extract Input sources from decorator"""
        inputs = []
        if isinstance(decorator, ast.Call) and len(decorator.args) > 1:
            # Second argument is typically Input(s)
            second_arg = decorator.args[1]
            inputs.extend(self._parse_dash_dependency(second_arg, 'Input'))
        return inputs
    
    def _parse_dash_dependency(self, node: ast.AST, dep_type: str) -> List[str]:
        """Parse Dash Input/Output dependencies"""
        dependencies = []
        
        if isinstance(node, ast.Call):
            # Single dependency like Output('id', 'children')
            if len(node.args) >= 2:
                component_id = self._extract_string_value(node.args[0])
                property_name = self._extract_string_value(node.args[1])
                if component_id and property_name:
                    dependencies.append(f"{component_id}.{property_name}")
        elif isinstance(node, (ast.List, ast.Tuple)):
            # Multiple dependencies
            for item in node.elts:
                dependencies.extend(self._parse_dash_dependency(item, dep_type))
        
        return dependencies
    
    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from AST node"""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        return None
    
    def _calculate_complexity_score(self, func_node: ast.FunctionDef, output_count: int, input_count: int) -> int:
        """Calculate complexity score for callback"""
        # Count function lines, nested if statements, loops, etc.
        complexity = 1  # Base complexity
        complexity += output_count * 2  # Outputs add complexity
        complexity += input_count  # Inputs add some complexity
        
        # Count AST nodes for function complexity
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                complexity += 2
            elif isinstance(node, ast.Try):
                complexity += 3
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
                complexity += 1
        
        return complexity
    
    def _analyze_output_conflicts(self) -> List[ConflictAnalysis]:
        """Analyze potential output conflicts"""
        conflicts = []
        
        for output_id, usages in self.output_conflicts.items():
            if len(usages) > 1:
                # Check if conflicts are intentional (allow_duplicate)
                severity = self._assess_conflict_severity(output_id, usages)
                
                conflict = ConflictAnalysis(
                    output_id=output_id,
                    conflicting_files=[usage['file'] for usage in usages],
                    conflicting_callbacks=[usage['callback_id'] for usage in usages if usage['callback_id']],
                    severity=severity,
                    resolution_suggestion=self._suggest_conflict_resolution(output_id, usages)
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _assess_conflict_severity(self, output_id: str, usages: List[dict]) -> str:
        """Assess the severity of output conflicts"""
        # Critical UI components
        if any(critical in output_id.lower() for critical in ['navbar', 'main', 'error', 'auth', 'login']):
            return 'HIGH'
        
        # More than 2 callbacks targeting same output
        if len(usages) > 2:
            return 'HIGH'
        
        # Different files targeting same output
        unique_files = set(usage['file'] for usage in usages)
        if len(unique_files) > 1:
            return 'MEDIUM'
        
        return 'LOW'
    
    def _suggest_conflict_resolution(self, output_id: str, usages: List[dict]) -> str:
        """Suggest resolution for conflicts"""
        if len(usages) > 2:
            return "CONSOLIDATE: Merge into single callback or split outputs"
        elif len(set(usage['file'] for usage in usages)) > 1:
            return "REFACTOR: Move callbacks to same module or use allow_duplicate=True"
        else:
            return "REVIEW: Check if allow_duplicate=True is appropriate"
    
    def _generate_summary(self) -> dict:
        """Generate comprehensive summary"""
        total_callbacks = len(self.patterns)
        
        return {
            'total_callbacks': total_callbacks,
            'pattern_distribution': dict(self.pattern_counts),
            'files_with_callbacks': len(set(p.file_path for p in self.patterns)),
            'unique_namespaces': len(self.namespace_usage),
            'total_conflicts': len(self.conflicts),
            'high_severity_conflicts': len([c for c in self.conflicts if c.severity == 'HIGH']),
            'average_complexity': sum(p.complexity_score for p in self.patterns) / max(total_callbacks, 1),
            'most_complex_callbacks': sorted(
                [(p.function_name, p.complexity_score, p.file_path) for p in self.patterns],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def _analyze_namespaces(self) -> dict:
        """Analyze namespace usage patterns"""
        namespace_stats = {}
        
        for namespace, callback_ids in self.namespace_usage.items():
            namespace_stats[namespace] = {
                'callback_count': len(callback_ids),
                'unique_callbacks': len(set(callback_ids)),
                'has_duplicates': len(callback_ids) != len(set(callback_ids)),
                'callback_ids': callback_ids
            }
        
        return namespace_stats
    
    def _assess_unicode_risks(self) -> List[dict]:
        """Assess Unicode-related risks in callbacks"""
        unicode_risks = []
        
        for pattern in self.patterns:
            # Check for string handling in function names or complex callbacks
            if pattern.complexity_score > 5:
                risk = {
                    'file': pattern.file_path,
                    'callback_id': pattern.callback_id,
                    'function_name': pattern.function_name,
                    'risk_level': 'MEDIUM' if pattern.complexity_score > 10 else 'LOW',
                    'reason': 'Complex callback may have string handling that needs Unicode safety'
                }
                unicode_risks.append(risk)
        
        return unicode_risks
    
    def _generate_consolidation_recommendations(self) -> List[str]:
        """Generate specific consolidation recommendations"""
        recommendations = []
        
        # Pattern consolidation recommendations
        if self.pattern_counts['legacy_dash'] > 0:
            recommendations.append(
                f"🔥 HIGH PRIORITY: Migrate {self.pattern_counts['legacy_dash']} legacy @app.callback patterns to TrulyUnifiedCallbacks"
            )
        
        if self.pattern_counts['callback_registry'] > 0:
            recommendations.append(
                f"⚡ MEDIUM PRIORITY: Consolidate {self.pattern_counts['callback_registry']} CallbackRegistry patterns"
            )
        
        # Conflict recommendations
        high_conflicts = [c for c in self.conflicts if c.severity == 'HIGH']
        if high_conflicts:
            recommendations.append(
                f"⚠️  URGENT: Resolve {len(high_conflicts)} high-severity output conflicts"
            )
        
        # Namespace recommendations
        if len(self.namespace_usage) > 20:
            recommendations.append(
                "📁 ORGANIZE: Consider consolidating namespaces - you have many small namespaces"
            )
        
        # Complexity recommendations
        complex_callbacks = [p for p in self.patterns if p.complexity_score > 15]
        if complex_callbacks:
            recommendations.append(
                f"🧩 REFACTOR: {len(complex_callbacks)} callbacks have high complexity scores - consider breaking them down"
            )
        
        # Unicode safety recommendations
        if any(risk['risk_level'] == 'MEDIUM' for risk in self._assess_unicode_risks()):
            recommendations.append(
                "🔒 UNICODE SAFETY: Implement Unicode-safe wrappers for complex callbacks"
            )
        
        return recommendations
    
    def generate_detailed_report(self, results: dict) -> str:
        """Generate comprehensive audit report"""
        report = "# 🎯 COMPREHENSIVE CALLBACK AUDIT REPORT\n\n"
        
        # Summary section
        summary = results['summary']
        report += "## 📊 EXECUTIVE SUMMARY\n\n"
        report += f"**Total Callbacks Found:** {summary['total_callbacks']:,}\n"
        report += f"**Files with Callbacks:** {summary['files_with_callbacks']:,}\n"
        report += f"**Unique Namespaces:** {summary['unique_namespaces']:,}\n"
        report += f"**Output Conflicts:** {summary['total_conflicts']:,} ({summary['high_severity_conflicts']} high priority)\n"
        report += f"**Average Complexity Score:** {summary['average_complexity']:.1f}\n\n"
        
        # Pattern distribution
        report += "## 📈 PATTERN DISTRIBUTION\n\n"
        for pattern_type, count in summary['pattern_distribution'].items():
            percentage = (count / summary['total_callbacks']) * 100
            report += f"- **{pattern_type.replace('_', ' ').title()}:** {count:,} callbacks ({percentage:.1f}%)\n"
        
        # Conflicts analysis
        if results['conflicts']:
            report += "\n## ⚠️  OUTPUT CONFLICTS ANALYSIS\n\n"
            for conflict in results['conflicts']:
                report += f"### {conflict.output_id} ({conflict.severity} PRIORITY)\n"
                report += f"- **Conflicting Files:** {', '.join(set(conflict.conflicting_files))}\n"
                report += f"- **Conflicting Callbacks:** {', '.join(filter(None, conflict.conflicting_callbacks))}\n"
                report += f"- **Resolution:** {conflict.resolution_suggestion}\n\n"
        
        # Namespace analysis
        report += "\n## 📁 NAMESPACE ANALYSIS\n\n"
        namespace_analysis = results['namespace_analysis']
        for namespace, stats in sorted(namespace_analysis.items(), key=lambda x: x[1]['callback_count'], reverse=True)[:10]:
            report += f"- **{namespace}:** {stats['callback_count']} callbacks"
            if stats['has_duplicates']:
                report += " ⚠️  (has duplicate callback IDs)"
            report += "\n"
        
        # Top recommendations
        report += "\n## 🚀 TOP RECOMMENDATIONS\n\n"
        for i, recommendation in enumerate(results['recommendations'][:5], 1):
            report += f"{i}. {recommendation}\n"
        
        # Most complex callbacks
        if summary['most_complex_callbacks']:
            report += "\n## 🧩 MOST COMPLEX CALLBACKS\n\n"
            for func_name, complexity, file_path in summary['most_complex_callbacks']:
                report += f"- **{func_name}** (Score: {complexity}) - `{file_path}`\n"
        
        # Unicode risks
        unicode_risks = results['unicode_risks']
        medium_risks = [r for r in unicode_risks if r['risk_level'] == 'MEDIUM']
        if medium_risks:
            report += "\n## 🔒 UNICODE SAFETY RISKS\n\n"
            for risk in medium_risks:
                report += f"- **{risk['function_name']}** in `{risk['file']}` - {risk['reason']}\n"
        
        report += "\n## 📋 NEXT STEPS\n\n"
        report += "1. **Address High Priority Conflicts** - Start with output conflicts marked as HIGH\n"
        report += "2. **Migrate Legacy Patterns** - Convert @app.callback to TrulyUnifiedCallbacks\n"
        report += "3. **Implement Unicode Safety** - Add Unicode-safe wrappers to complex callbacks\n"
        report += "4. **Consolidate Patterns** - Standardize on single registration approach\n"
        report += "5. **Performance Monitoring** - Add metrics to track callback performance\n"
        
        return report
    
    def save_results(self, results: dict, output_dir: str = "callback_audit_results"):
        """Save audit results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save main report
        report = self.generate_detailed_report(results)
        with open(output_path / "callback_audit_report.md", 'w') as f:
            f.write(report)
        
        # Save raw data as JSON
        # Convert objects to dictionaries for JSON serialization
        json_results = {
            'summary': results['summary'],
            'pattern_counts': dict(self.pattern_counts),
            'conflicts': [
                {
                    'output_id': c.output_id,
                    'conflicting_files': c.conflicting_files,
                    'conflicting_callbacks': c.conflicting_callbacks,
                    'severity': c.severity,
                    'resolution_suggestion': c.resolution_suggestion
                }
                for c in results['conflicts']
            ],
            'patterns': [
                {
                    'file_path': p.file_path,
                    'line_number': p.line_number,
                    'pattern_type': p.pattern_type,
                    'callback_id': p.callback_id,
                    'component_name': p.component_name,
                    'function_name': p.function_name,
                    'complexity_score': p.complexity_score,
                    'output_targets': p.output_targets,
                    'input_sources': p.input_sources
                }
                for p in self.patterns
            ]
        }
        
        with open(output_path / "callback_audit_data.json", 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"📁 Results saved to {output_path}/")
        print(f"📄 Report: {output_path}/callback_audit_report.md")
        print(f"📊 Data: {output_path}/callback_audit_data.json")

# Usage example
if __name__ == "__main__":
    auditor = YourSystemCallbackAuditor()
    results = auditor.scan_complete_codebase()
    
    # Print summary to console
    print("\n" + "="*50)
    print("CALLBACK AUDIT SUMMARY")
    print("="*50)
    summary = results['summary']
    print(f"Total Callbacks: {summary['total_callbacks']:,}")
    print(f"Pattern Types: {len(summary['pattern_distribution'])}")
    print(f"Conflicts: {summary['total_conflicts']} ({summary['high_severity_conflicts']} high priority)")
    print(f"Files Analyzed: {summary['files_with_callbacks']}")
    
    print("\nPattern Distribution:")
    for pattern_type, count in summary['pattern_distribution'].items():
        print(f"  {pattern_type}: {count}")
    
    print("\nTop Recommendations:")
    for i, rec in enumerate(results['recommendations'][:3], 1):
        print(f"  {i}. {rec}")
    
    # Save detailed results
    auditor.save_results(results)
    
    print(f"\n✅ Audit complete! Check callback_audit_results/ for detailed analysis.")