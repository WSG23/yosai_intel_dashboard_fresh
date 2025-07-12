#!/usr/bin/env python3
"""
UI CALLBACK TRACER
Add this to your deep analytics callbacks to trace what's actually being called
"""

# Add this to pages/deep_analytics/callbacks.py - at the top after imports
import logging

logger = logging.getLogger(__name__)

# MODIFIED VERSION: Add logging to ALL callback functions


def run_unique_patterns_analysis():
    """TRACED: Run unique patterns analysis using the analytics service."""
    logger.info("🔥 UI CALLBACK: run_unique_patterns_analysis() called")

    try:
        analytics_service = AnalyticsService()
        logger.info("🔥 UI: Calling analytics_service.get_unique_patterns_analysis()")

        results = analytics_service.get_unique_patterns_analysis()

        logger.info(f"🔥 UI: Got results with status: {results.get('status')}")

        if results["status"] == "success":
            data_summary = results["data_summary"]
            total_records = data_summary.get("total_records", 0)

            logger.info(f"🔥 UI: data_summary total_records = {total_records:,}")

            # Check if this is where 150 comes from
            if total_records == 150:
                logger.error("🚨 UI: FOUND 150 ROW LIMIT in UI callback results!")

            user_patterns = results["user_patterns"]
            device_patterns = results["device_patterns"]
            interaction_patterns = results["interaction_patterns"]
            temporal_patterns = results["temporal_patterns"]
            access_patterns = results["access_patterns"]
            recommendations = results["recommendations"]

            # Log what's being displayed
            logger.info(
                f"🔥 UI: Building display with {total_records:,} in Database Overview card"
            )

            return html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Database Overview",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{data_summary['total_records']:,}",
                                                className="text-primary",
                                            ),
                                            html.P("Total Access Events"),
                                            html.Small(
                                                f"Spanning {data_summary['date_range']['span_days']} days"
                                            ),
                                        ]
                                    ),
                                    color="light",
                                ),
                                width=3,
                            ),
                            # ... rest of the UI components
                        ]
                    )
                ]
            )
        else:
            logger.error(f"🔥 UI: Error in results: {results}")
            return dbc.Alert(
                f"Analysis failed: {results.get('message', 'Unknown error')}",
                color="danger",
            )

    except Exception as e:
        logger.error(f"🔥 UI: Exception in run_unique_patterns_analysis: {e}")
        import traceback

        traceback.print_exc()
        return dbc.Alert(f"Analysis error: {str(e)}", color="danger")


# Also add tracing to other analysis functions
def run_service_analysis_traced(data_source: str, analysis_type: str):
    """TRACED: Service analysis with logging"""
    logger.info(
        f"🔥 UI CALLBACK: run_service_analysis called with {analysis_type} for {data_source}"
    )

    results = analyze_data_with_service_safe(data_source, analysis_type)

    total_events = results.get("total_events", 0)
    logger.info(f"🔥 UI: Service analysis returned {total_events:,} total events")

    if total_events == 150:
        logger.error("🚨 UI: FOUND 150 ROW LIMIT in service analysis!")

    if isinstance(results, dict) and "error" in results:
        return dbc.Alert(str(results["error"]), color="danger")

    return create_analysis_results_display_safe(results, analysis_type)


# =============================================================================
# BROWSER CONSOLE JAVASCRIPT TRACER
# =============================================================================

"""
Add this JavaScript to your browser console to trace button clicks:

// Button click tracer - paste this in browser console
document.addEventListener('click', function(e) {
    if (e.target.textContent.includes('Unique Patterns') || 
        e.target.textContent.includes('Security') ||
        e.target.textContent.includes('Trends')) {
        console.log('🔥 BUTTON CLICKED:', e.target.textContent);
        console.log('🔥 BUTTON ID:', e.target.id);
        console.log('🔥 BUTTON CLASSES:', e.target.className);
    }
});

// Callback tracer - logs all Dash callbacks
if (window.dash_clientside) {
    const originalUpdate = window.dash_clientside.callback_update;
    window.dash_clientside.callback_update = function(...args) {
        console.log('🔥 DASH CALLBACK:', args);
        return originalUpdate.apply(this, args);
    };
}
"""

# =============================================================================
# QUICK CHECK SCRIPT
# =============================================================================


def check_ui_data_source():
    """Quick check of what data the UI can access"""
    print("🔍 UI DATA SOURCE CHECK")
    print("=" * 40)

    # Check uploaded data
    try:
        from services.upload_data_service import get_uploaded_data

        uploaded_data = get_uploaded_data()

        print(f"📁 Uploaded files available to UI:")
        for filename, df in uploaded_data.items():
            print(f"   {filename}: {len(df):,} rows")

    except Exception as e:
        print(f"❌ Error accessing uploaded data: {e}")

    # Check analytics service
    try:
        from services import AnalyticsService

        service = AnalyticsService()

        # Test the method
        result = service.get_unique_patterns_analysis()
        total = result.get("data_summary", {}).get("total_records", 0)

        print(f"⚙️  Analytics service method returns: {total:,} total records")

    except Exception as e:
        print(f"❌ Error testing analytics service: {e}")


if __name__ == "__main__":
    check_ui_data_source()
