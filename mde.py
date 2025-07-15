#!/usr/bin/env python3
"""
MVP Data Enhancement Tool - Thin Shell Around Existing Base Code
Tests the complete upload flow using existing project architecture
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path  
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import logging

# Import existing base code (no custom implementations)
from config.service_registration import register_upload_services
from core.service_container import ServiceContainer
from services.upload import UploadProcessingService
from components.file_preview import create_file_preview_ui
from services.upload.utils.file_parser import create_file_preview
from services.data_enhancer import get_ai_column_suggestions
from services.device_learning_service import DeviceLearningService
from analytics.db_interface import AnalyticsDataAccessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MVPTestApp:
    """Minimal test wrapper around existing base code"""
    
    def __init__(self):
        self.container = ServiceContainer()
        self.upload_service = None
        self.learning_service = None
        self.analytics_accessor = None
        self.session_data = {}
        
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
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "MVP Data Enhancement - Base Code Test"
        
        # Simple layout testing the complete flow
        self.app.layout = dbc.Container([
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
            
            # Hidden stores
            dcc.Store(id="session-store", data={})
        ], fluid=True)
        
        self._register_callbacks()
    
    def _register_callbacks(self):
        """Register callbacks using base code services"""
        
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                upload_results, preview_components, file_info = loop.run_until_complete(
                    self.upload_service.process_uploaded_files([contents], [filename])
                )
                loop.close()
                
                logger.info(f"✅ Base code processing complete")
                
                # Extract processed data  
                df = None
                ai_suggestions = {}
                
                if filename in file_info:
                    info = file_info[filename]
                    ai_suggestions = info.get('ai_suggestions', {})
                    
                    # Get the stored dataframe
                    try:
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
                column_display = self._create_column_display(ai_suggestions, df)
                device_display = self._create_device_display(df, filename)
                data_display = self._create_data_display(df)
                
                return upload_display, column_display, device_display, data_display, session_data
                
            except Exception as e:
                logger.error(f"💥 Upload processing failed: {e}")
                error_display = dbc.Alert(f"Processing failed: {str(e)}", color="danger")
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
            ctx = dash.callback_context
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
    
    def _create_column_display(self, ai_suggestions, df):
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
        """Create device analysis display using base code"""
        if df is None or df.empty:
            return dbc.Alert("No device data available", color="info")
        
        # Use base code device learning service
        try:
            device_mappings = self.learning_service.get_user_device_mappings(filename)
            
            if device_mappings:
                device_list = [html.Li(f"{device}: {attrs}") for device, attrs in device_mappings.items()]
                return html.Div([
                    html.H6("🚪 Learned Device Mappings:"),
                    html.Ul(device_list[:10])  # Show first 10
                ])
            else:
                return dbc.Alert("No learned device mappings found", color="info")
                
        except Exception as e:
            return dbc.Alert(f"Device analysis error: {str(e)}", color="warning")
    
    def _create_data_display(self, df):
        """Create data preview using base code"""
        if df is None or df.empty:
            return dbc.Alert("No data to display", color="info")
        
        # Use base code file preview functions
        try:
            preview_info = create_file_preview(df)
            return create_file_preview_ui(preview_info)
        except Exception as e:
            logger.error(f"Preview creation failed: {e}")
            # Fallback to simple table
            return dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{"name": col, "id": col} for col in df.columns],
                style_table={'overflowX': 'auto'}
            )
    
    def run(self, debug=True, host='0.0.0.0', port=5003):
        """Run the test app"""
        logger.info("🚀 Starting MVP Data Enhancement Tool - Base Code Test")
        logger.info(f"🌐 Access: http://localhost:{port}")
        self.app.run_server(debug=debug, host=host, port=port)

if __name__ == '__main__':
    # Create and run the minimal test app
    app = MVPTestApp()
    app.run()
