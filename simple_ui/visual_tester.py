#!/usr/bin/env python3
"""
Visual Testing Interface for Yōsai Intel Dashboard
A simple Streamlit UI to test the complete pipeline visually
"""

import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path
from config.app_config import UploadConfig
import asyncio
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Apply our fixes
def apply_all_fixes():
    """Apply all the fixes we developed"""
    try:
        # Step 1: Callback fix
        from core.callback_manager import CallbackManager
        if hasattr(CallbackManager, 'handle_register') and not hasattr(CallbackManager, 'register_handler'):
            CallbackManager.register_handler = CallbackManager.handle_register
        
        # Step 2: Missing methods fix
        from services.upload_processing import UploadAnalyticsProcessor
        
        if not hasattr(UploadAnalyticsProcessor, 'get_analytics_from_uploaded_data'):
            def get_analytics_from_uploaded_data(self):
                try:
                    data = self.load_uploaded_data()
                    if not data:
                        return {"status": "no_data", "message": "No uploaded files available"}
                    result = self._process_uploaded_data_directly(data)
                    result["status"] = "success"
                    return result
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            UploadAnalyticsProcessor.get_analytics_from_uploaded_data = get_analytics_from_uploaded_data
        
        if not hasattr(UploadAnalyticsProcessor, 'clean_uploaded_dataframe'):
            def clean_uploaded_dataframe(self, df):
                cleaned_df = df.dropna(how='all').copy()
                cleaned_df.columns = [col.strip().replace(' ', '_').lower() for col in cleaned_df.columns]
                return cleaned_df
            UploadAnalyticsProcessor.clean_uploaded_dataframe = clean_uploaded_dataframe
            
        if not hasattr(UploadAnalyticsProcessor, 'summarize_dataframe'):
            def summarize_dataframe(self, df):
                return {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                    "null_counts": df.isnull().sum().to_dict()
                }
            UploadAnalyticsProcessor.summarize_dataframe = summarize_dataframe
        
        return True
    except Exception as e:
        st.error(f"Failed to apply fixes: {e}")
        return False

# Apply fixes
apply_all_fixes()

def main():
    st.set_page_config(
        page_title="Yōsai Intel Dashboard - Visual Tester",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏢 Yōsai Intel Dashboard - Visual Testing Interface")
    st.markdown("### Complete Pipeline Testing: File Processing → AI Mapping → Analytics")
    
    # Sidebar navigation
    st.sidebar.title("🧪 Testing Modules")
    
    test_mode = st.sidebar.selectbox(
        "Select Test Module:",
        [
            "🏠 Dashboard Overview",
            "📁 File Processing",
            "🗺️ Device Mapping Viewer", 
            "📊 Analytics Engine",
            "🔍 Real-Time Analysis"
        ]
    )
    
    if test_mode == "🏠 Dashboard Overview":
        show_dashboard_overview()
    elif test_mode == "📁 File Processing":
        show_file_processing()
    elif test_mode == "🗺️ Device Mapping Viewer":
        show_device_mapping()
    elif test_mode == "📊 Analytics Engine":
        show_analytics_engine()
    elif test_mode == "🔍 Real-Time Analysis":
        show_realtime_analysis()

def show_dashboard_overview():
    st.header("🏠 Dashboard Overview")
    
    # System health check
    with st.expander("🔧 System Health Check", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        try:
            from services.analytics_service import AnalyticsService
            analytics = AnalyticsService()
            health = analytics.health_check()
            
            with col1:
                if health.get('service') == 'healthy':
                    st.success("✅ Analytics Service")
                else:
                    st.error("❌ Analytics Service")
                    
            with col2:
                if health.get('database') == 'healthy':
                    st.success("✅ Database")
                else:
                    st.error("❌ Database")
                    
            with col3:
                files = health.get('uploaded_files', 0)
                if files > 0:
                    st.success(f"✅ {files} Uploaded Files")
                else:
                    st.warning("⚠️ No Uploaded Files")
                    
        except Exception as e:
            st.error(f"Health check failed: {e}")
    
    # Quick stats
    st.subheader("📈 Quick Statistics")
    
    try:
        # Load Enhanced Security Demo data
        parquet_path = Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Access Events", len(df))
            with col2:
                st.metric("Unique Employees", df['Employee Code'].nunique())
            with col3:
                st.metric("Unique Doors", df['Door Location'].nunique())
            with col4:
                granted = len(df[df['Entry Status'] == 'Granted'])
                st.metric("Access Granted", f"{granted}/{len(df)}")
        else:
            st.info("Load Enhanced Security Demo data to see statistics")
            
    except Exception as e:
        st.error(f"Statistics error: {e}")
    
    # Device mappings overview
    st.subheader("🗺️ Device Mappings Overview")
    
    try:
        from services.device_learning_service import DeviceLearningService
        device_service = DeviceLearningService()
        mappings = device_service.learned_mappings
        
        if mappings:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Learned Mappings", len(mappings))
            
            with col2:
                enhanced_mappings = [k for k, v in mappings.items() if 'Enhanced_Security_Demo' in str(v.get('filename', ''))]
                st.metric("Enhanced Demo Mappings", len(enhanced_mappings))
            
            # Show recent mappings
            st.write("**Recent Mappings:**")
            for i, (key, value) in enumerate(list(mappings.items())[:3]):
                filename = value.get('filename', 'Unknown')
                device_count = value.get('device_count', 0)
                st.write(f"• {filename}: {device_count} devices")
                
        else:
            st.warning("No device mappings found")
            
    except Exception as e:
        st.error(f"Device mapping overview error: {e}")

def show_file_processing():
    st.header("📁 File Processing Module")
    
    st.write("Test file upload and processing capabilities")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file to test processing",
        type=['csv', 'json', 'xlsx', 'xls'],
        help="Upload CSV, JSON, or Excel files to test the processing pipeline"
    )
    
    if uploaded_file is not None:
        try:
            # Process the file
            with st.spinner("Processing file..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.json'):
                    df = pd.read_json(uploaded_file)
                elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                
            st.success(f"✅ File processed successfully!")
            
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Memory (MB)", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f}")
            
            # Show column info
            st.subheader("Column Information")
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes,
                'Non-Null': df.count(),
                'Null Count': df.isnull().sum()
            })
            st.dataframe(col_info)
            
            # Show sample data
            st.subheader("Sample Data")
            st.dataframe(df.head(10))
            
            # Test AI suggestions
            st.subheader("🤖 AI Column Suggestions")
            if st.button("Get AI Suggestions"):
                try:
                    from services.data_enhancer import get_ai_column_suggestions
                    suggestions = get_ai_column_suggestions(df)
                    
                    if suggestions:
                        for col, suggestion in suggestions.items():
                            field = suggestion.get('field', '')
                            confidence = suggestion.get('confidence', 0)
                            if field and confidence > 0:
                                st.write(f"• **{col}** → `{field}` (confidence: {confidence:.1f})")
                    else:
                        st.info("No AI suggestions available")
                        
                except Exception as e:
                    st.error(f"AI suggestions failed: {e}")
            
        except Exception as e:
            st.error(f"File processing failed: {e}")

def show_device_mapping():
    st.header("🗺️ Device Mapping Viewer")
    st.write("Explore your learned device mappings and building layout")
    
    try:
        from services.device_learning_service import DeviceLearningService
        device_service = DeviceLearningService()
        mappings = device_service.learned_mappings
        
        if not mappings:
            st.warning("No device mappings found")
            return
        
        # Select mapping to view
        mapping_options = {
            f"{key} ({value.get('filename', 'Unknown')} - {value.get('device_count', 0)} devices)": key 
            for key, value in mappings.items()
        }
        
        selected_mapping = st.selectbox("Select Mapping to View:", list(mapping_options.keys()))
        
        if selected_mapping:
            mapping_key = mapping_options[selected_mapping]
            mapping_data = mappings[mapping_key]
            
            # Show mapping details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Filename", mapping_data.get('filename', 'Unknown'))
            with col2:
                st.metric("Device Count", mapping_data.get('device_count', 0))
            with col3:
                saved_at = mapping_data.get('saved_at', '')
                st.metric("Saved", saved_at[:10] if saved_at else 'Unknown')
            
            # Show device mappings
            device_mappings = mapping_data.get('device_mappings', {})
            
            if device_mappings:
                st.subheader("🚪 Device Details")
                
                # Create DataFrame for better visualization
                device_data = []
                for device_name, details in device_mappings.items():
                    device_data.append({
                        'Device': device_name,
                        'Floor': details.get('floor_number', 'N/A'),
                        'Security Level': details.get('security_level', 'N/A'),
                        'Entry Point': '✅' if details.get('is_entry') else '❌',
                        'Exit Point': '✅' if details.get('is_exit') else '❌',
                        'Restricted': '🔒' if details.get('is_restricted') else '🔓',
                        'Confidence': details.get('confidence', 0)
                    })
                
                device_df = pd.DataFrame(device_data)
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    floor_filter = st.multiselect("Filter by Floor:", sorted(device_df['Floor'].unique()))
                with col2:
                    security_filter = st.multiselect("Filter by Security Level:", sorted(device_df['Security Level'].unique()))
                
                # Apply filters
                filtered_df = device_df.copy()
                if floor_filter:
                    filtered_df = filtered_df[filtered_df['Floor'].isin(floor_filter)]
                if security_filter:
                    filtered_df = filtered_df[filtered_df['Security Level'].isin(security_filter)]
                
                st.dataframe(filtered_df, use_container_width=True)
                
                # Visualizations
                st.subheader("📊 Device Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Security level distribution
                    security_counts = device_df['Security Level'].value_counts()
                    fig = px.bar(
                        x=security_counts.index, 
                        y=security_counts.values,
                        title="Devices by Security Level",
                        labels={'x': 'Security Level', 'y': 'Count'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Floor distribution
                    floor_counts = device_df['Floor'].value_counts()
                    fig = px.pie(
                        values=floor_counts.values,
                        names=floor_counts.index,
                        title="Devices by Floor"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Device mapping viewer error: {e}")

def show_analytics_engine():
    st.header("📊 Analytics Engine")
    st.write("Test analytics capabilities with your data")
    
    # Initialize analytics
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
        
        # Load Enhanced Security Demo data
        parquet_path = Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            
            st.success(f"✅ Loaded Enhanced Security Demo: {len(df)} access events")
            
            # Analytics tests
            tests = {
                "🏠 Dashboard Summary": lambda: analytics.get_dashboard_summary(),
                "🔍 Access Patterns": lambda: analytics.analyze_access_patterns(days=1),
                "⚠️ Anomaly Detection": lambda: analytics.detect_anomalies(df),
                "🧹 Data Processing": lambda: analytics.clean_uploaded_dataframe(df),
                "📈 Data Summary": lambda: analytics.summarize_dataframe(df),
                "📊 Uploaded Analytics": lambda: analytics.get_analytics_from_uploaded_data(),
            }
            
            for test_name, test_func in tests.items():
                with st.expander(f"{test_name}", expanded=False):
                    if st.button(f"Run {test_name}", key=test_name):
                        try:
                            with st.spinner(f"Running {test_name}..."):
                                result = test_func()
                            
                            st.success("✅ Test completed!")
                            
                            if isinstance(result, pd.DataFrame):
                                st.write(f"**Result**: DataFrame with {len(result)} rows")
                                st.dataframe(result.head())
                            elif isinstance(result, dict):
                                st.json(result)
                            elif isinstance(result, list):
                                st.write(f"**Result**: List with {len(result)} items")
                                if result:
                                    st.write(result[:5])  # Show first 5 items
                                else:
                                    st.write("Empty list")
                            else:
                                st.write(f"**Result**: {result}")
                                
                        except Exception as e:
                            st.error(f"❌ Test failed: {e}")
            
        else:
            st.warning("Enhanced Security Demo data not found. Upload data to test analytics.")
            
    except Exception as e:
        st.error(f"Analytics engine initialization failed: {e}")

def show_realtime_analysis():
    st.header("🔍 Real-Time Analysis")
    st.write("Interactive analysis of your Enhanced Security Demo data")
    
    try:
        # Load data
        parquet_path = Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        if not parquet_path.exists():
            st.warning("Enhanced Security Demo data not found")
            return
            
        df = pd.read_parquet(parquet_path)
        
        # Data overview
        st.subheader("📊 Data Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", len(df))
        with col2:
            st.metric("Unique Employees", df['Employee Code'].nunique())
        with col3:
            st.metric("Unique Doors", df['Door Location'].nunique())
        with col4:
            granted_pct = (len(df[df['Entry Status'] == 'Granted']) / len(df)) * 100
            st.metric("Access Rate", f"{granted_pct:.1f}%")
        
        # Time analysis
        st.subheader("⏰ Time Analysis")
        df['Event Time'] = pd.to_datetime(df['Event Time'])
        df['Hour'] = df['Event Time'].dt.hour
        df['Minute'] = df['Event Time'].dt.minute
        
        hourly_activity = df['Hour'].value_counts().sort_index()
        
        fig = px.bar(
            x=hourly_activity.index,
            y=hourly_activity.values,
            title="Access Activity by Hour",
            labels={'x': 'Hour of Day', 'y': 'Number of Access Events'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top locations
        st.subheader("🚪 Most Active Locations")
        location_counts = df['Door Location'].value_counts().head(10)
        
        fig = px.bar(
            x=location_counts.values,
            y=location_counts.index,
            orientation='h',
            title="Top 10 Most Accessed Doors",
            labels={'x': 'Access Count', 'y': 'Door Location'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Employee activity
        st.subheader("👥 Employee Activity")
        employee_counts = df['Employee Code'].value_counts().head(10)
        
        fig = px.bar(
            x=employee_counts.index,
            y=employee_counts.values,
            title="Most Active Employees",
            labels={'x': 'Employee Code', 'y': 'Access Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Interactive filters
        st.subheader("🔍 Interactive Filtering")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_status = st.multiselect(
                "Filter by Entry Status:",
                df['Entry Status'].unique(),
                default=df['Entry Status'].unique()
            )
        
        with col2:
            hour_range = st.slider(
                "Filter by Hour Range:",
                min_value=int(df['Hour'].min()),
                max_value=int(df['Hour'].max()),
                value=(int(df['Hour'].min()), int(df['Hour'].max()))
            )
        
        # Apply filters
        filtered_df = df[
            (df['Entry Status'].isin(selected_status)) &
            (df['Hour'] >= hour_range[0]) &
            (df['Hour'] <= hour_range[1])
        ]
        
        st.write(f"**Filtered Data**: {len(filtered_df)} events")
        st.dataframe(filtered_df.head(20))
        
    except Exception as e:
        st.error(f"Real-time analysis error: {e}")

if __name__ == "__main__":
    main()
