"""
Analytics Integration Guide
Provides specific integration instructions and replacement code for existing dashboard
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

# Import the new analytics controller
from .analytics_controller import (
    AnalyticsController, 
    AnalyticsConfig, 
    create_analytics_controller,
    create_performance_controller
)

class DashboardAnalyticsIntegration:
    """
    Integration layer for existing dashboard components
    Provides drop-in replacements for existing analytics functions
    """
    
    def __init__(self):
        # Create optimized controller for dashboard use
        self.controller = create_performance_controller()
        
        # Register callbacks for dashboard updates
        self._setup_dashboard_callbacks()
    
    def _setup_dashboard_callbacks(self):
        """Setup callbacks for dashboard integration"""
        
        def on_analysis_progress(analysis_id: str, analysis_type: str, progress: float):
            # Update dashboard progress indicators
            print(f"Analysis Progress: {analysis_type} - {progress:.1f}%")
        
        def on_analysis_complete(analysis_id: str, result):
            # Trigger dashboard refresh
            print(f"Analysis {analysis_id} completed successfully")
        
        def on_analysis_error(analysis_id: str, error):
            # Show error message in dashboard
            print(f"Analysis {analysis_id} failed: {error}")
        
        # Register callbacks
        self.controller.register_callback('on_analysis_progress', on_analysis_progress)
        self.controller.register_callback('on_analysis_complete', on_analysis_complete)
        self.controller.register_callback('on_analysis_error', on_analysis_error)


# =============================================================================
# REPLACEMENT CODE FOR EXISTING DASHBOARD COMPONENTS
# =============================================================================

"""
STEP 1: Replace existing analytics function in pages/deep_analytics.py
"""

def replace_generate_analytics(uploaded_data: pd.DataFrame, 
                               analysis_type: str, 
                               data_source: str) -> tuple:
    """
    REPLACEMENT for generate_analytics() function in pages/deep_analytics.py
    
    ORIGINAL LOCATION: pages/deep_analytics.py, line ~50
    ORIGINAL FUNCTION: generate_analytics(uploaded_data, analysis_type, data_source)
    
    REPLACEMENT INSTRUCTIONS:
    1. Find the existing generate_analytics() function
    2. Replace the entire function body with this code
    3. Keep the same function signature
    4. Update any imports at the top of the file
    """
    
    try:
        # Create analytics controller
        controller = create_performance_controller()
        
        # Map old analysis types to new system
        analysis_mapping = {
            'security': ['security_patterns'],
            'trends': ['access_trends'],
            'behavior': ['user_behavior'],
            'anomaly': ['anomaly_detection']
        }
        
        # Get specific analysis types
        requested_analyses = analysis_mapping.get(analysis_type, ['security_patterns'])
        
        # Run analytics
        results = controller.analyze_specific(uploaded_data, requested_analyses)
        
        # Format results for existing dashboard components
        formatted_results = _format_results_for_dashboard(results, analysis_type, data_source)
        
        # Return in expected format: (success_component, results_dict)
        success_message = f"✅ Analysis completed successfully! Processed {len(uploaded_data):,} events."
        
        return success_message, formatted_results
        
    except Exception as e:
        error_message = f"❌ Analysis failed: {str(e)}"
        return error_message, {}


def _format_results_for_dashboard(results: Dict[str, Any], 
                                  analysis_type: str, 
                                  data_source: str) -> Dict[str, Any]:
    """
    Format new analytics results to match existing dashboard expectations
    """
    
    # Base structure expected by existing dashboard
    formatted = {
        'analysis_type': analysis_type,
        'analysis_focus': _get_analysis_focus(analysis_type),
        'data_source': data_source,
        'generated_at': datetime.now().isoformat(),
        'total_events': 0,
        'processing_time': 0.0
    }
    
    # Add specific results based on analysis type
    if analysis_type == 'security' and 'security_patterns' in results:
        security_data = results['security_patterns']
        formatted.update({
            'security_metrics': {
                'security_score': security_data.get('security_score', 0),
                'failed_attempts': security_data.get('failed_access_patterns', {}).get('total', 0),
                'suspicious_patterns': security_data.get('threat_summary', {}).get('threat_count', 0)
            },
            'security_patterns': security_data
        })
    
    elif analysis_type == 'trends' and 'access_trends' in results:
        trends_data = results['access_trends']
        formatted.update({
            'trend_metrics': {
                'daily_average': trends_data.get('trend_summary', {}).get('daily_average_events', 0),
                'events_per_user': trends_data.get('trend_summary', {}).get('events_per_user_average', 0),
                'peak_activity': _extract_peak_activity(trends_data)
            },
            'trends': trends_data
        })
    
    elif analysis_type == 'behavior' and 'user_behavior' in results:
        behavior_data = results['user_behavior']
        formatted.update({
            'behavior_metrics': {
                'active_users': behavior_data.get('behavior_summary', {}).get('total_unique_users', 0),
                'average_access_per_user': behavior_data.get('behavior_summary', {}).get('avg_events_per_user', 0),
                'behavioral_anomalies': len(behavior_data.get('behavioral_anomalies', {}).get('user_anomalies', {}))
            },
            'user_behavior': behavior_data
        })
    
    elif analysis_type == 'anomaly' and 'anomaly_detection' in results:
        anomaly_data = results['anomaly_detection']
        anomaly_summary = anomaly_data.get('anomaly_summary', {})
        risk_assessment = anomaly_data.get('risk_assessment', {})
        
        formatted.update({
            'anomaly_metrics': {
                'total_anomalies': anomaly_summary.get('total_anomalies', 0),
                'anomaly_rate': _calculate_anomaly_rate(anomaly_data),
                'critical_anomalies': _count_critical_anomalies(anomaly_data)
            },
            'anomalies': anomaly_data,
            'risk_level': risk_assessment.get('risk_level', 'low')
        })
    
    return formatted


"""
STEP 2: Replace analytics dropdown population in pages/deep_analytics.py
"""

def replace_analytics_dropdown_options():
    """
    REPLACEMENT for analytics dropdown options
    
    ORIGINAL LOCATION: pages/deep_analytics.py, analytics_type dropdown options
    ORIGINAL CODE: dcc.Dropdown options list
    
    REPLACEMENT INSTRUCTIONS:
    1. Find the analytics_type dropdown component
    2. Replace the 'options' parameter with this list
    """
    
    return [
        {"label": "🔒 Security Patterns Analysis", "value": "security"},
        {"label": "📈 Access Trends Analysis", "value": "trends"}, 
        {"label": "👤 User Behavior Analysis", "value": "behavior"},
        {"label": "🚨 Anomaly Detection", "value": "anomaly"},
        {"label": "📊 Interactive Charts", "value": "charts"}
    ]


"""
STEP 3: Add new charts integration function
"""

def get_interactive_charts(uploaded_data: pd.DataFrame) -> Dict[str, Any]:
    """
    NEW FUNCTION to add to pages/deep_analytics.py
    
    INTEGRATION INSTRUCTIONS:
    1. Add this function to pages/deep_analytics.py
    2. Import it in the callback section
    3. Call it when analysis_type == 'charts'
    """
    
    try:
        controller = create_performance_controller()
        
        # Generate all charts
        chart_results = controller.analyze_specific(uploaded_data, ['interactive_charts'])
        
        if 'interactive_charts' in chart_results:
            return chart_results['interactive_charts']
        else:
            return {}
            
    except Exception as e:
        print(f"Chart generation failed: {e}")
        return {}


"""
STEP 4: Enhanced callback replacement for deep_analytics.py
"""

def replace_analytics_callback():
    """
    REPLACEMENT for the main analytics callback in pages/deep_analytics.py
    
    ORIGINAL LOCATION: pages/deep_analytics.py, @app.callback decorator around line 150
    ORIGINAL FUNCTION: update_analytics_content()
    
    REPLACEMENT INSTRUCTIONS:
    1. Find the existing callback function (likely update_analytics_content)
    2. Replace the entire function body with this enhanced version
    3. Keep the same callback decorator and function signature
    """
    
    callback_code = '''
@app.callback(
    [Output('analytics-content', 'children'),
     Output('analytics-store', 'data')],
    [Input('analytics-button', 'n_clicks')],
    [State('analytics-type', 'value'),
     State('data-source', 'value'),
     State('analytics-store', 'data')]
)
def update_analytics_content(n_clicks, analysis_type, data_source, stored_data):
    """Enhanced analytics callback with new modular system"""
    
    if not n_clicks or not analysis_type or not data_source:
        return html.Div("Select analysis type and data source, then click 'Run Analytics'"), {}
    
    try:
        # Get uploaded data (implement your data loading logic here)
        uploaded_data = get_uploaded_data(data_source)  # Your existing function
        
        if uploaded_data is None or uploaded_data.empty:
            return create_error_alert("No data available for analysis"), {}
        
        # Special handling for interactive charts
        if analysis_type == 'charts':
            chart_results = get_interactive_charts(uploaded_data)
            charts_content = create_charts_dashboard(chart_results)
            return charts_content, {'charts': chart_results}
        
        # Run standard analytics
        success_msg, results = replace_generate_analytics(uploaded_data, analysis_type, data_source)
        
        # Create dashboard content
        content = create_analytics_dashboard(results, analysis_type, success_msg)
        
        return content, results
        
    except Exception as e:
        error_content = create_error_alert(f"Analytics failed: {str(e)}")
        return error_content, {}
'''
    
    return callback_code


"""
STEP 5: Dashboard content creation functions
"""

def create_charts_dashboard(chart_results: Dict[str, Any]):
    """
    NEW FUNCTION to create charts dashboard
    
    INTEGRATION INSTRUCTIONS:
    1. Add this function to pages/deep_analytics.py
    2. Import required Dash components (dcc, html, dbc)
    3. Use this for displaying interactive charts
    """
    
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    if not chart_results:
        return html.Div("No charts available")
    
    components = []
    
    # Security Onion Model
    if 'onion_model' in chart_results:
        onion_data = chart_results['onion_model']
        if 'onion_model' in onion_data:
            components.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("🧅 Security Onion Model")),
                    dbc.CardBody([
                        dcc.Graph(figure=onion_data['onion_model'])
                    ])
                ], className="mb-4")
            )
    
    # Security Overview Charts
    if 'security_overview' in chart_results:
        overview_charts = chart_results['security_overview']
        for chart_name, figure in overview_charts.items():
            components.append(
                dbc.Card([
                    dbc.CardHeader(html.H5(f"📊 {chart_name.replace('_', ' ').title()}")),
                    dbc.CardBody([
                        dcc.Graph(figure=figure)
                    ])
                ], className="mb-4")
            )
    
    # Risk Dashboard
    if 'risk_dashboard' in chart_results:
        risk_charts = chart_results['risk_dashboard']
        for chart_name, figure in risk_charts.items():
            components.append(
                dbc.Card([
                    dbc.CardHeader(html.H5(f"⚠️ {chart_name.replace('_', ' ').title()}")),
                    dbc.CardBody([
                        dcc.Graph(figure=figure)
                    ])
                ], className="mb-4")
            )
    
    return html.Div(components)


"""
STEP 6: Testing and validation functions
"""

class AnalyticsModuleTester:
    """
    Testing utilities for analytics modules
    
    USAGE INSTRUCTIONS:
    1. Create an instance: tester = AnalyticsModuleTester()
    2. Run tests: tester.test_all_modules(your_data)
    3. Check results: tester.get_test_results()
    """
    
    def __init__(self):
        self.test_results = {}
        self.controller = create_analytics_controller()
    
    def test_security_patterns(self, df: pd.DataFrame) -> bool:
        """Test security patterns module"""
        try:
            results = self.controller.analyze_specific(df, ['security_patterns'])
            success = 'security_patterns' in results and bool(results['security_patterns'])
            self.test_results['security_patterns'] = {
                'success': success,
                'error': None if success else 'No results returned'
            }
            return success
        except Exception as e:
            self.test_results['security_patterns'] = {'success': False, 'error': str(e)}
            return False
    
    def test_access_trends(self, df: pd.DataFrame) -> bool:
        """Test access trends module"""
        try:
            results = self.controller.analyze_specific(df, ['access_trends'])
            success = 'access_trends' in results and bool(results['access_trends'])
            self.test_results['access_trends'] = {
                'success': success,
                'error': None if success else 'No results returned'
            }
            return success
        except Exception as e:
            self.test_results['access_trends'] = {'success': False, 'error': str(e)}
            return False
    
    def test_user_behavior(self, df: pd.DataFrame) -> bool:
        """Test user behavior module"""
        try:
            results = self.controller.analyze_specific(df, ['user_behavior'])
            success = 'user_behavior' in results and bool(results['user_behavior'])
            self.test_results['user_behavior'] = {
                'success': success,
                'error': None if success else 'No results returned'
            }
            return success
        except Exception as e:
            self.test_results['user_behavior'] = {'success': False, 'error': str(e)}
            return False
    
    def test_anomaly_detection(self, df: pd.DataFrame) -> bool:
        """Test anomaly detection module"""
        try:
            results = self.controller.analyze_specific(df, ['anomaly_detection'])
            success = 'anomaly_detection' in results and bool(results['anomaly_detection'])
            self.test_results['anomaly_detection'] = {
                'success': success,
                'error': None if success else 'No results returned'
            }
            return success
        except Exception as e:
            self.test_results['anomaly_detection'] = {'success': False, 'error': str(e)}
            return False
    
    def test_interactive_charts(self, df: pd.DataFrame) -> bool:
        """Test interactive charts module"""
        try:
            results = self.controller.analyze_specific(df, ['interactive_charts'])
            success = 'interactive_charts' in results and bool(results['interactive_charts'])
            self.test_results['interactive_charts'] = {
                'success': success,
                'error': None if success else 'No results returned'
            }
            return success
        except Exception as e:
            self.test_results['interactive_charts'] = {'success': False, 'error': str(e)}
            return False
    
    def test_all_modules(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Test all analytics modules"""
        results = {
            'security_patterns': self.test_security_patterns(df),
            'access_trends': self.test_access_trends(df),
            'user_behavior': self.test_user_behavior(df),
            'anomaly_detection': self.test_anomaly_detection(df),
            'interactive_charts': self.test_interactive_charts(df)
        }
        
        print("=== ANALYTICS MODULE TEST RESULTS ===")
        for module, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{module}: {status}")
            if not success and module in self.test_results:
                print(f"  Error: {self.test_results[module]['error']}")
        
        return results
    
    def get_test_results(self) -> Dict[str, Any]:
        """Get detailed test results"""
        return self.test_results


# Helper functions for dashboard integration

def _get_analysis_focus(analysis_type: str) -> str:
    """Get analysis focus label"""
    focus_map = {
        'security': 'Security Patterns',
        'trends': 'Access Trends', 
        'behavior': 'User Behavior Analysis',
        'anomaly': 'Anomaly Detection',
        'charts': 'Interactive Charts'
    }
    return focus_map.get(analysis_type, 'General Analysis')

def _extract_peak_activity(trends_data: Dict[str, Any]) -> str:
    """Extract peak activity information"""
    peak_analysis = trends_data.get('peak_analysis', {})
    peak_hours = peak_analysis.get('peak_hours', [])
    
    if peak_hours:
        return f"{peak_hours[0]}:00 - {peak_hours[-1]}:00"
    else:
        return "Unknown"

def _calculate_anomaly_rate(anomaly_data: Dict[str, Any]) -> float:
    """Calculate anomaly rate percentage"""
    # This would need actual total events count from original data
    # For now, return a placeholder calculation
    total_anomalies = anomaly_data.get('anomaly_summary', {}).get('total_anomalies', 0)
    return min(total_anomalies * 0.1, 10.0)  # Placeholder calculation

def _count_critical_anomalies(anomaly_data: Dict[str, Any]) -> int:
    """Count critical anomalies"""
    severity_breakdown = anomaly_data.get('anomaly_summary', {}).get('severity_breakdown', {})
    return severity_breakdown.get('critical', 0)


# =============================================================================
# INTEGRATION CHECKLIST
# =============================================================================

integration_checklist = """
ANALYTICS INTEGRATION CHECKLIST
===============================

☐ 1. IMPORT STATEMENTS
   Add to top of pages/deep_analytics.py:
   from analytics.integration_guide import (
       replace_generate_analytics, 
       replace_analytics_dropdown_options,
       get_interactive_charts,
       create_charts_dashboard,
       AnalyticsModuleTester
   )

☐ 2. REPLACE EXISTING FUNCTIONS
   - Replace generate_analytics() function body
   - Update analytics dropdown options
   - Replace main analytics callback

☐ 3. ADD NEW FUNCTIONS  
   - Add get_interactive_charts() function
   - Add create_charts_dashboard() function
   - Add charts option to dropdown

☐ 4. UPDATE IMPORTS
   Ensure these modules are available:
   - analytics.security_patterns
   - analytics.access_trends  
   - analytics.user_behavior
   - analytics.anomaly_detection
   - analytics.interactive_charts
   - analytics.analytics_controller

☐ 5. TEST INTEGRATION
   - Create test data
   - Run AnalyticsModuleTester
   - Verify all modules load correctly
   - Test each analysis type

☐ 6. VERIFY DASHBOARD
   - Check all dropdown options work
   - Verify charts display correctly
   - Test error handling
   - Confirm callback updates

☐ 7. PERFORMANCE OPTIMIZATION
   - Enable caching if needed
   - Configure parallel processing
   - Adjust sensitivity settings
   - Monitor memory usage

TESTING COMMAND:
===============
# Run this in your Python console to test
tester = AnalyticsModuleTester()
test_results = tester.test_all_modules(your_test_data)
print("All tests passed:", all(test_results.values()))
"""

print(integration_checklist)

# Export key functions and classes
__all__ = [
    'DashboardAnalyticsIntegration',
    'replace_generate_analytics',
    'replace_analytics_dropdown_options', 
    'get_interactive_charts',
    'create_charts_dashboard',
    'replace_analytics_callback',
    'AnalyticsModuleTester'
]
