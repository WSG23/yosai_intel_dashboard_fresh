import re

print("Replacing custom UI with base code components...")
with open("mde.py", "r") as f:
    content = f.read()

# Add imports for base code UI components
new_imports = """
from components.column_verification import create_column_verification_modal
from components.simple_device_mapping import create_simple_device_modal_with_ai
"""

content = re.sub(
    r"(from analytics\.db_interface import AnalyticsDataAccessor)",
    r"\1" + new_imports,
    content,
)

# Replace custom column display with base code modal
new_column_display = '''
    def _create_column_display(self, ai_suggestions, df):
        """Use base code column verification component"""
        if not ai_suggestions or df is None:
            return dbc.Alert("No AI suggestions available", color="info")
        
        # Prepare file_info for base code component
        file_info = {
            'filename': self.session_data.get('filename', 'uploaded_file.csv'),
            'columns': df.columns.tolist(),
            'ai_suggestions': ai_suggestions
        }
        
        # Use base code column verification modal
        modal = create_column_verification_modal(file_info)
        
        return html.Div([
            html.H6("🤖 AI Column Suggestions:"),
            html.P(f"Found {len(ai_suggestions)} AI suggestions"),
            dbc.Button("Configure Column Mapping", id="open-column-modal", color="primary"),
            modal,
            dbc.Alert("Using base code column verification component", color="info")
        ])'''

content = re.sub(
    r"def _create_column_display\(self, ai_suggestions, df\):.*?return html\.Div\(\[.*?\]\)",
    new_column_display,
    content,
    flags=re.DOTALL,
)

# Replace custom device display with base code modal
new_device_display = '''
    def _create_device_display(self, df, filename):
        """Use base code device mapping component"""
        if df is None or df.empty:
            return dbc.Alert("No device data available", color="info")
        
        try:
            # Extract unique devices from data
            device_columns = [
                col
                for col in df.columns
                if any(term in str(col).lower() for term in ["door", "device", "location"])
            ]
            devices = [
                device
                for col in device_columns
                for device in df[col].dropna().unique().tolist()
            ]
            
            if devices:
                # Use base code device modal
                device_modal = create_simple_device_modal_with_ai(devices[:10])  # First 10 devices
                
                return html.Div([
                    html.H6(f"🚪 Device Analysis ({len(devices)} devices found):"),
                    html.P(f"Devices: {', '.join(devices[:5])}{'...' if len(devices) > 5 else ''}"),
                    dbc.Button("Configure Device Mapping", id="open-device-modal", color="info"),
                    device_modal,
                    dbc.Alert("Using base code device mapping component", color="info")
                ])
            else:
                return dbc.Alert("No devices found in data", color="warning")
                
        except Exception as e:
            return dbc.Alert(f"Device analysis error: {str(e)}", color="warning")'''

content = re.sub(
    r'def _create_device_display\(self, df, filename\):.*?return dbc\.Alert\(f"Device analysis error: \{str\(e\)\}", color="warning"\)',
    new_device_display,
    content,
    flags=re.DOTALL,
)

with open("mde.py", "w") as f:
    f.write(content)

print("✅ Replaced custom UI with base code components")
