#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVP Data Enhancement Tool - Thin Shell Around Existing Base Code
Tests the complete upload flow using existing project architecture
"""

def safe_str(obj):
    """Handle unicode and encoding issues."""
    try:
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return str(obj).encode('utf-8', errors='ignore').decode('utf-8', errors='replace')
    except:
        return repr(obj)

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, safe_str(PROJECT_ROOT))

import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import dash_table

import pandas as pd
import dash_bootstrap_components as dbc
from components.column_verification import (
    create_complete_column_section,
    register_callbacks as register_column_callbacks,
)
from components.simple_device_mapping import (
    register_callbacks as register_device_callbacks,
)
from core.master_callback_system import MasterCallbackSystem
import logging
from services.base_database_service import BaseDatabaseService

# Import existing base code (no custom implementations)
from config.service_registration import register_upload_services
from core.service_container import ServiceContainer
from services.upload import UploadProcessingService
from components.file_preview import create_file_preview_ui
from services.upload.utils.file_parser import create_file_preview
from services.data_enhancer.mapping_utils import get_ai_column_suggestions
from services.device_learning_service import DeviceLearningService
from analytics.db_interface import AnalyticsDataAccessor

# Module logger configured in __main__
logger = logging.getLogger(__name__)

class MVPTestApp(BaseDatabaseService):
    """Minimal test wrapper around existing base code"""
    
    def __init__(self) -> None:
        super().__init__(None)
        self.container = ServiceContainer()
        self.upload_service: UploadProcessingService | None = None
        self.learning_service: DeviceLearningService | None = None
        self.analytics_accessor: AnalyticsDataAccessor | None = None
        self.session_data: dict = {}
        
        self._initialize_services()
        self._create_app()
    
    def _initialize_services(self):
        """Initialize using existing base code service registration"""
        try:
            # Use existing service registration
            register_upload_services(self.container)
            
            # Get services from container
            self.upload_service = self.container.get("upload_processor")
            self.learning_service = self.container.get("device_learning_service") 
            
            # Initialize analytics
            self.analytics_accessor = AnalyticsDataAccessor()
            
            logger.info("✅ All base code services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            raise
    
    def _create_app(self):
        """Create Dash app with minimal layout"""
        self.app = dash.Dash(
            name=__name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )
        self.app.title = "MVP Data Enhancement - Base Code Test"  # type: ignore[attr-defined]

        # Manager allowing callbacks for dynamically created components
        self.callback_manager = MasterCallbackSystem(self.app)
        
        # Simple layout testing the complete flow
        self.app.layout = dbc.Container([  # type: ignore[attr-defined]
            dbc.Row([
                dbc.Col([
                    html.H1("MVP Data Enhancement Tool", className="text-center mb-4"),
                    html.P("Testing Complete Base Code Flow", className="text-center text-muted mb-4"),
                ])
            ]),
            
            # Upload Section
            dbc.Card([
                dbc.CardHeader(html.H4("File Upload")),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-area',
                        children=html.Div(['Drag & Drop or Click to Upload CSV/Excel/JSON']),
                        style={
                            'width': '100%', 'height': '100px', 'lineHeight': '100px',
                            'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                            'textAlign': 'center', 'margin': '10px'
                        }
                    )
                ])
            ], className="mb-4"),
            
            # Results Section  
            dbc.Card([
                dbc.CardHeader(html.H4("Processing Results")),
                dbc.CardBody([
                    html.Div(id="upload-results")
                ])
            ], className="mb-4"),
            
            # Column Mapping Section
            dbc.Card([
                dbc.CardHeader(html.H4("AI Column Mapping")),
                dbc.CardBody([
                    html.Div(id="column-mapping")
                ])
            ], className="mb-4"),
            
            # Device Analysis Section
            dbc.Card([
                dbc.CardHeader(html.H4("Device Analysis")),
                dbc.CardBody([
                    html.Div(id="device-analysis")
                ])
            ], className="mb-4"),
            
            # Enhanced Data Section
            dbc.Card([
                dbc.CardHeader(html.H4("Enhanced Data")),
                dbc.CardBody([
                    html.Div(id="enhanced-data")
                ])
            ], className="mb-4"),
            
            # Export Section
            dbc.Card([
                dbc.CardHeader(html.H4("Export")),
                dbc.CardBody([
                    dbc.ButtonGroup([
                        dbc.Button("Download CSV", id="download-csv", color="primary"),
                        dbc.Button("Download JSON", id="download-json", color="info"),
                    ]),
                    dcc.Download(id="download-component")
                ])
            ]),
            
            # Device Verification Modal (base code pattern)
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Device Classification")),
                dbc.ModalBody("", id="device-modal-body"),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="device-verify-cancel", color="secondary"),
                    dbc.Button("Confirm", id="device-verify-confirm", color="success"),
                ])
            ], id="device-verification-modal", is_open=False, size="xl"),
            

            # Hidden stores
            dcc.Store(id="session-store", data={})
        ], fluid=True)
        
        self._register_callbacks()
    
    def _register_callbacks(self):
        """Register callbacks using base code services"""
        
        # Register column verification callbacks
        try:
            register_column_callbacks(self.callback_manager)
            logger.info("✅ Column verification callbacks registered")
        except Exception as e:
            logger.warning(f"⚠️ Column verification callbacks failed: {e}")

        # Register device mapping callbacks
        try:
            register_device_callbacks(self.callback_manager)
            logger.info("✅ Device mapping callbacks registered")
        except Exception as e:
            logger.warning(f"⚠️ Device mapping callbacks failed: {e}")
        
        @self.app.callback(
            [Output('upload-results', 'children'),
             Output('column-mapping', 'children'),
             Output('device-analysis', 'children'),
             Output('enhanced-data', 'children'),
             Output('session-store', 'data')],
            [Input('upload-area', 'contents')],
            [State('upload-area', 'filename'),
             State('session-store', 'data')]
        )
        def handle_upload(contents, filename, session_data):
            """Process upload using existing base code"""
            if not contents:
                return "", "", "", "", session_data
            
            try:
                logger.info(f"📁 Processing file: {filename}")
                
                # Use existing base code upload service
                assert self.upload_service is not None
                result_dict = asyncio.run(
                    self.upload_service.process_uploaded_files([contents], [filename])
                )
                
                # Extract from flexible dictionary
                upload_results = result_dict.get('upload_results', [])
                preview_components = result_dict.get('file_preview_components', [])
                file_info = result_dict.get('file_info_dict', {})
                
                logger.info(f"✅ Base code processing complete")
                
                # Extract processed data  
                df = None
                ai_suggestions = {}
                
                if filename in file_info:
                    info = file_info[filename]
                    ai_suggestions = info.get('ai_suggestions', {})
                    
                    # Get the stored dataframe
                    try:
                        assert self.upload_service is not None
                        stored_data = self.upload_service.store.get_all_data()
                        df = stored_data.get(filename)
                        logger.info(f"📊 Retrieved DataFrame: {df.shape if df is not None else 'None'}")
                    except Exception as e:
                        logger.warning(f"Could not retrieve stored data: {e}")
                
                # Update session
                session_data.update({
                    'df': df.to_dict('records') if df is not None else [],
                    'columns': df.columns.tolist() if df is not None else [],
                    'filename': filename,
                    'ai_suggestions': ai_suggestions,
                    'file_info': file_info
                })
                
                # Create displays using base code
                upload_display = self._create_upload_display(upload_results, file_info.get(filename, {}))
                column_display = self.create_column_display(ai_suggestions, df)
                device_display = self._create_device_display(df, filename)
                data_display = self._create_data_display(df)
                
                return upload_display, column_display, device_display, data_display, session_data
                
            except Exception as e:
                logger.error(f"💥 Upload processing failed: {e}")
                error_display = dbc.Alert(f"Processing failed: {safe_str(e)}", color="danger")
                return error_display, "", "", "", session_data
        
        @self.app.callback(
            Output('download-component', 'data'),
            [Input('download-csv', 'n_clicks'),
             Input('download-json', 'n_clicks')],
            [State('session-store', 'data')],
            prevent_initial_call=True
        )
        def handle_download(csv_clicks, json_clicks, session_data):
            """Handle download using base code"""
            ctx = callback_context
            if not ctx.triggered or not session_data.get('df'):
                return dash.no_update
            
            # Reconstruct DataFrame from session
            df = pd.DataFrame(session_data['df'])
            filename = session_data.get('filename', 'data')
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'download-csv':
                return dcc.send_data_frame(df.to_csv, f"enhanced_{filename}.csv", index=False)
            elif button_id == 'download-json':
                return dcc.send_data_frame(df.to_json, f"enhanced_{filename}.json", orient='records')
            
            return dash.no_update
    
    def _create_upload_display(self, upload_results, file_info):
        """Create upload results display using base code"""
        if not file_info:
            return dbc.Alert("No file information available", color="warning")
        
        return dbc.Alert([
            html.H5("✅ Upload Successful!", className="mb-2"),
            html.P(f"File: {file_info.get('filename', 'Unknown')}"),
            html.P(f"Rows: {file_info.get('rows', 0):,}"),
            html.P(f"Columns: {file_info.get('columns', 0)}")
        ], color="success")
    
    def create_column_display(self, ai_suggestions, df):
        """Use base code for complete column mapping interface"""
        # Get current file info for base code
        file_info = {
            'ai_suggestions': ai_suggestions,
            'column_names': df.columns.tolist() if df is not None else [],
            'columns': len(df.columns) if df is not None else 0,
            'filename': 'Test1.csv'
        }
        return create_complete_column_section(file_info, df)

        """Create AI column mapping display"""
        if not ai_suggestions:
            return dbc.Alert("No AI suggestions available", color="info")
        
        suggestions_list = []
        for column, suggestion in ai_suggestions.items():
            field = suggestion.get('field', '')
            confidence = suggestion.get('confidence', 0)
            if field:
                suggestions_list.append(
                    html.Li(f"{column} → {field} ({confidence:.0%} confidence)")
                )
        
        if not suggestions_list:
            return dbc.Alert("No confident AI suggestions found", color="warning")
        
        return html.Div([
            html.H6("🤖 AI Column Suggestions:"),
            html.Ul(suggestions_list),
            dbc.Alert("AI suggestions generated by base code", color="info")
        ])
    
    def _create_device_display(self, df, filename):
        """Create device mapping UI with buttons (mirror base code exactly)"""
        if df is None or df.empty:
            return dbc.Alert("No device data available", color="info")
        
        try:
            # Mirror the exact base code upload processor flow
            assert self.learning_service is not None
            user_mappings = self.learning_service.get_user_device_mappings(filename)
            
            if user_mappings:
                # Load user mappings into ai_mapping_store (exactly like base code)
                from services.ai_mapping_store import ai_mapping_store
                ai_mapping_store.clear()
                for device, mapping in user_mappings.items():
                    mapping["source"] = "user_confirmed" 
                    ai_mapping_store.set(device, mapping)
                
                logger.info(f"✅ Loaded {len(user_mappings)} saved mappings - AI SKIPPED")
            else:
                # No user mappings - use auto_apply_learned_mappings (exactly like base code)
                from services.ai_mapping_store import ai_mapping_store
                ai_mapping_store.clear()
                
                # Mirror base code auto_apply_learned_mappings call
                assert self.upload_service is not None
                learned_applied = self.upload_service.auto_apply_learned_mappings(df, filename)
                
                if not learned_applied:
                    # Generate AI device defaults for new files (base code pattern)
                    from components import simple_device_mapping as sdm
                    sdm.generate_ai_device_defaults(df, "auto")
                    logger.info("🤖 Generated AI device defaults for new file")
            
            # Create device mapping UI section (base code pattern)
            from components import simple_device_mapping as sdm
            device_section = sdm.create_device_mapping_section()
            
            # Add status information
            store_data = ai_mapping_store.all()
            status_alert = dbc.Alert(
                f"📋 {len(store_data)} devices ready for mapping" if store_data
                else "🔍 No devices found in uploaded data", 
                color="info"
            )
            
            return html.Div([
                html.H6("🚪 Device Configuration:"),
                status_alert,
                device_section
            ])
                    
        except Exception as e:
            return dbc.Alert(f"Device mapping error: {safe_str(e)}", color="warning")

    def _create_data_display(self, df):
        """Create data configuration UI with preview and action buttons."""
        if df is None or df.empty:
            return dbc.Alert("No data to display", color="info")

        # Mirror base code build_file_preview_component exactly
        from services.upload.utils.file_parser import create_file_preview
        from components.file_preview import create_file_preview_ui

        try:
            preview_info = create_file_preview(df)
            preview_ui = create_file_preview_ui(preview_info)

            # Add base code Data Configuration card with button group
            config_card = dbc.Card([
                dbc.CardHeader([html.H6("📋 Data Configuration", className="mb-0")]),
                dbc.CardBody([
                    html.P("Configure your data for analysis:", className="mb-3"),
                    dbc.ButtonGroup([
                        dbc.Button(
                            "📋 Verify Columns",
                            id="verify-columns-btn-simple",
                            color="primary",
                            size="sm",
                        ),
                        dbc.Button(
                            "🤖 Classify Devices",
                            id="classify-devices-btn",
                            color="info",
                            size="sm",
                        ),
                    ], className="w-100"),
                ]),
            ])

            return html.Div([preview_ui, config_card])

        except Exception as e:
            logger.error(f"Preview creation failed: {e}")
            # Fallback to simple table
            return dash_table.DataTable(
                data=df.head(10).to_dict("records"),
                columns=[{"name": col, "id": col} for col in df.columns],
                style_table={"overflowX": "auto"},
            )
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Create and run the minimal test app
    app = MVPTestApp()

    # Test device analysis using existing base code
    print("\n=== DEVICE ANALYSIS ===")
    from services.device_learning_service import DeviceLearningService
    
    device_service = DeviceLearningService()
    learned_mappings = device_service.learned_mappings
    
    if learned_mappings:
        print(f"📋 Learned Device Mappings:")
        
        # Extract all device mappings using existing base code structure
        all_device_mappings = {}
        for fingerprint, data in learned_mappings.items():
            device_mappings = data.get("device_mappings", {})
            filename = data.get("filename", "Unknown")
            for device_name, properties in device_mappings.items():
                properties["source_file"] = filename
                all_device_mappings[device_name] = properties
        
        # Display device mappings (like your screenshot)
        for device_name, props in all_device_mappings.items():
            print(f"• {device_name}: {props}")
            
        print(f"\n✅ Found {len(all_device_mappings)} learned device mappings")
    else:
        print("📋 No learned device mappings found")
    
    # Start the web UI after device analysis
    print("\n=== STARTING WEB UI ===")
    print("🌐 Device analysis complete - launching web interface...")
    app.app.run()  # type: ignore[attr-defined]
