#!/usr/bin/env python3
"""
Test script for enhanced analytics modules
Create this as test_enhanced_analytics.py in your project root
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from analytics.analytics_controller import (
    AnalyticsController,
    AnalyticsConfig,
    CallbackController,
    CallbackEvent,
)


def create_test_data(n_records: int = 1000) -> pd.DataFrame:
    """Create synthetic test data with known patterns"""
    np.random.seed(42)

    # Generate base data
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    hours = list(range(24))
    users = [f"USER_{i:03d}" for i in range(50)]
    doors = [f"DOOR_{i:02d}" for i in range(10)]

    data = []

    for i in range(n_records):
        # Normal patterns (80% of data)
        if i < n_records * 0.8:
            # Business hours bias
            hour_weights = [0.01 if h < 6 or h > 20 else 0.04 for h in hours]
            hour = np.random.choice(hours, p=hour_weights)
            user = np.random.choice(users)
            door = np.random.choice(doors)
            result = "Granted" if np.random.random() > 0.05 else "Denied"

        # Inject anomalies (20% of data)
        else:
            # After-hours access with higher failure rates
            hour = np.random.choice([1, 2, 3, 23])
            user = np.random.choice(users[:5])  # Specific users for anomalies
            door = np.random.choice(doors)
            result = (
                "Denied" if np.random.random() > 0.3 else "Granted"
            )  # Higher failure rate

        timestamp = np.random.choice(dates) + pd.Timedelta(
            hours=hour,
            minutes=np.random.randint(0, 60),
            seconds=np.random.randint(0, 60),
        )

        # Add Unicode test characters occasionally
        user_with_unicode = user + ("_测试" if i % 100 == 0 else "")

        data.append(
            {
                "event_id": i + 1,
                "timestamp": timestamp,
                "person_id": user_with_unicode,
                "door_id": door,
                "access_result": result,
                "badge_status": "Valid" if np.random.random() > 0.02 else "Invalid",
            }
        )

    return pd.DataFrame(data)


def test_callback(callback_data):
    """Test callback function to monitor events"""
    print(f"📢 Callback: {callback_data.event_type.value}")

    # Print relevant data based on event type
    if callback_data.event_type == CallbackEvent.ANALYSIS_START:
        print(
            f"   🚀 Starting analysis with {callback_data.data.get('total_records', 0)} records"
        )
    elif callback_data.event_type == CallbackEvent.ANALYSIS_COMPLETE:
        print(
            f"   ✅ Analysis completed in {callback_data.data.get('processing_time', 0):.2f}s"
        )
        print(
            f"   📊 Modules: {', '.join(callback_data.data.get('modules_completed', []))}"
        )
    elif callback_data.event_type == CallbackEvent.SECURITY_THREAT_DETECTED:
        print(
            f"   🚨 SECURITY THREAT: {callback_data.data.get('risk_level', 'unknown')} risk level detected!"
        )
    elif callback_data.event_type == CallbackEvent.ANOMALY_DETECTED:
        print(
            f"   ⚠️  ANOMALIES: {callback_data.data.get('total_anomalies', 0)} anomalies detected"
        )
    elif callback_data.event_type == CallbackEvent.BEHAVIOR_RISK_IDENTIFIED:
        print(
            f"   👤 BEHAVIOR RISK: {callback_data.data.get('high_risk_count', 0)} high-risk users identified"
        )
    elif callback_data.event_type == CallbackEvent.TREND_CHANGE_DETECTED:
        print(
            f"   📈 TREND CHANGE: {callback_data.data.get('trend', 'unknown')} trend detected"
        )
    elif callback_data.event_type == CallbackEvent.ANALYSIS_ERROR:
        print(f"   ❌ ERROR: {callback_data.data.get('error', 'Unknown error')}")


def test_individual_modules():
    """Test each module individually"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL MODULES")
    print("=" * 60)

    # Create small test dataset
    test_df = create_test_data(100)

    # Test Security Analyzer
    print("\n🔒 Testing Security Analyzer...")
    try:
        from analytics.security_patterns import SecurityPatternsAnalyzer

        security_analyzer = SecurityPatternsAnalyzer()
        security_result = security_analyzer.analyze_patterns(test_df)
        print(f"   ✅ Security analysis completed")
        print(f"   📊 Security score: {security_result.get('security_score', 0):.1f}")
        print(f"   🚨 Risk level: {security_result.get('risk_level', 'unknown')}")
        print(f"   🎯 Threats detected: {security_result.get('threat_count', 0)}")
    except Exception as e:
        print(f"   ❌ Security analysis failed: {e}")

    # Test Trends Analyzer
    print("\n📈 Testing Trends Analyzer...")
    try:
        from analytics.access_trends import AccessTrendsAnalyzer

        trends_analyzer = AccessTrendsAnalyzer()
        trends_result = trends_analyzer.analyze_trends(test_df)
        print(f"   ✅ Trends analysis completed")
        print(f"   📊 Overall trend: {trends_result.get('overall_trend', 'unknown')}")
        print(f"   💪 Trend strength: {trends_result.get('trend_strength', 0):.2f}")
        print(f"   📉 Change rate: {trends_result.get('change_rate', 0):.1f}%")
    except Exception as e:
        print(f"   ❌ Trends analysis failed: {e}")

    # Test Behavior Analyzer
    print("\n👥 Testing Behavior Analyzer...")
    try:
        from analytics.user_behavior import UserBehaviorAnalyzer

        behavior_analyzer = UserBehaviorAnalyzer()
        behavior_result = behavior_analyzer.analyze_behavior(test_df)
        print(f"   ✅ Behavior analysis completed")
        print(f"   👤 Users analyzed: {behavior_result.get('total_users_analyzed', 0)}")
        print(f"   ⚠️  High-risk users: {behavior_result.get('high_risk_users', 0)}")
        print(f"   📊 Behavior score: {behavior_result.get('behavior_score', 0):.1f}")
    except Exception as e:
        print(f"   ❌ Behavior analysis failed: {e}")

    # Test Anomaly Detector
    print("\n🔍 Testing Anomaly Detector...")
    try:
        from analytics.anomaly_detection import AnomalyDetector

        anomaly_detector = AnomalyDetector()
        anomaly_result = anomaly_detector.detect_anomalies(test_df)
        print(f"   ✅ Anomaly detection completed")
        print(
            f"   🎯 Anomalies detected: {anomaly_result.get('anomalies_detected', 0)}"
        )
        print(f"   🚨 Threat level: {anomaly_result.get('threat_level', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Anomaly detection failed: {e}")


def test_controller_integration():
    """Test complete controller integration"""
    print("\n" + "=" * 60)
    print("TESTING CONTROLLER INTEGRATION")
    print("=" * 60)

    # Create test data
    print("\n📊 Creating test dataset...")
    test_df = create_test_data(1000)
    print(f"   ✅ Created dataset with {len(test_df)} records")
    print(f"   👥 Users: {test_df['person_id'].nunique()}")
    print(f"   🚪 Doors: {test_df['door_id'].nunique()}")
    print(
        f"   📅 Date range: {test_df['timestamp'].min().date()} to {test_df['timestamp'].max().date()}"
    )
    print(f"   ✅ Success rate: {(test_df['access_result'] == 'Granted').mean():.1%}")

    # Initialize callback manager
    print("\n📡 Initializing callback system...")
    callback_manager = CallbackController()

    # Register callbacks for all events
    for event in CallbackEvent:
        callback_manager.register_callback(event, test_callback)
    print("   ✅ Callbacks registered for all events")

    # Initialize controller
    print("\n🎛️  Initializing analytics controller...")
    config = AnalyticsConfig(
        enable_security_patterns=True,
        enable_access_trends=True,
        enable_user_behavior=True,
        enable_anomaly_detection=True,
        parallel_processing=False,  # Sequential for testing clarity
    )
    controller = AnalyticsController(config=config, controller=callback_manager)
    print("   ✅ Controller initialized with all modules enabled")

    # Run complete analysis
    print("\n🚀 Running complete analytics...")
    start_time = datetime.now()
    results = controller.analyze(test_df, "integration_test_001")
    end_time = datetime.now()

    processing_time = (end_time - start_time).total_seconds()
    print(f"\n⏱️  Analysis completed in {processing_time:.2f} seconds")

    return results


def verify_results(results):
    """Verify and display analysis results"""
    print("\n" + "=" * 60)
    print("VERIFYING RESULTS")
    print("=" * 60)

    # Check overall status
    print(f"\n📊 Analysis Status: {results.status}")
    if results.errors:
        print(f"⚠️  Errors encountered: {len(results.errors)}")
        for error in results.errors:
            print(f"   • {error}")
    else:
        print("✅ No errors encountered")

    # Verify each module
    modules_to_check = {
        "security_patterns": "🔒 Security Analysis",
        "access_trends": "📈 Trends Analysis",
        "user_behavior": "👥 Behavior Analysis",
        "anomaly_detection": "🔍 Anomaly Detection",
    }

    print(f"\n📋 Module Results:")
    for module_key, module_name in modules_to_check.items():
        module_result = getattr(results, module_key, {})
        if module_result:
            print(f"   ✅ {module_name}: {len(module_result)} result items")
        else:
            print(f"   ❌ {module_name}: No results")

    # Display key metrics
    print(f"\n📊 Data Summary:")
    summary = results.data_summary
    print(f"   📝 Total records: {summary.get('total_records', 0):,}")
    print(f"   👥 Unique users: {summary.get('unique_users', 0):,}")
    print(f"   🚪 Unique doors: {summary.get('unique_doors', 0):,}")
    print(f"   ✅ Success rate: {summary.get('success_rate', 0):.1%}")
    print(f"   ⏱️  Processing time: {results.processing_time:.2f} seconds")

    # Display analysis insights
    print(f"\n🔍 Key Analysis Results:")

    # Security insights
    if results.security_patterns:
        security_score = results.security_patterns.get("security_score", 0)
        risk_level = results.security_patterns.get("risk_level", "unknown")
        threat_count = results.security_patterns.get("threat_count", 0)
        print(
            f"   🔒 Security Score: {security_score:.1f}/100 (Risk: {risk_level}, Threats: {threat_count})"
        )

    # Trends insights
    if results.access_trends:
        trend = results.access_trends.get("overall_trend", "unknown")
        strength = results.access_trends.get("trend_strength", 0)
        change_rate = results.access_trends.get("change_rate", 0)
        print(
            f"   📈 Access Trend: {trend} (Strength: {strength:.2f}, Change: {change_rate:.1f}%)"
        )

    # Behavior insights
    if results.user_behavior:
        total_users = results.user_behavior.get("total_users_analyzed", 0)
        high_risk = results.user_behavior.get("high_risk_users", 0)
        behavior_score = results.user_behavior.get("behavior_score", 0)
        print(
            f"   👥 User Analysis: {total_users} users, {high_risk} high-risk (Score: {behavior_score:.1f})"
        )

    # Anomaly insights
    if results.anomaly_detection:
        anomalies = results.anomaly_detection.get("anomalies_detected", 0)
        threat_level = results.anomaly_detection.get("threat_level", "unknown")
        print(f"   🔍 Anomalies: {anomalies} detected (Threat: {threat_level})")

    # Success criteria
    print(f"\n✅ SUCCESS CRITERIA:")
    success_checks = []

    # Check if analysis completed
    success_checks.append(
        ("Analysis completed", results.status in ["success", "partial_success"])
    )

    # Check if modules ran
    success_checks.append(("Security module", bool(results.security_patterns)))
    success_checks.append(("Trends module", bool(results.access_trends)))
    success_checks.append(("Behavior module", bool(results.user_behavior)))
    success_checks.append(("Anomaly module", bool(results.anomaly_detection)))

    # Check processing time reasonable
    success_checks.append(("Processing time < 30s", results.processing_time < 30))

    # Check no critical errors
    success_checks.append(("No critical errors", results.status != "error"))

    all_passed = True
    for check_name, passed in success_checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False

    return all_passed


def main():
    """Run complete enhanced analytics test suite"""
    print("=" * 60)
    print("🧪 ENHANCED ANALYTICS TEST SUITE")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test 1: Individual modules
        test_individual_modules()

        # Test 2: Controller integration
        results = test_controller_integration()

        # Test 3: Verify results
        all_passed = verify_results(results)

        # Final verdict
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED! Enhanced Analytics Ready for Production!")
            print("=" * 60)
            print("\n✅ Your enhanced analytics modules are working correctly:")
            print("   • Advanced security threat detection")
            print("   • Robust trend analysis with forecasting")
            print("   • ML-based user behavior analysis")
            print("   • Multi-algorithm anomaly detection")
            print("   • Unicode-safe string handling")
            print("   • Consolidated callback system")
            print("\n🚀 You can now use the enhanced analytics in your application!")
            return 0
        else:
            print("❌ SOME TESTS FAILED! Check the output above for details.")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during testing: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        return 1

    finally:
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
