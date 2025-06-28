"""
Interactive Charts Module
Creates comprehensive security dashboard charts including onion model
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
import json

class SecurityChartsGenerator:
    """Generate interactive security charts for dashboard"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.color_palette = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'info': '#17a2b8',
            'secondary': '#6c757d'
        }
        
    def generate_all_charts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate all interactive charts for security dashboard"""
        try:
            if df.empty:
                return self._empty_charts()
            
            df = self._prepare_data(df)
            
            charts = {
                'onion_model': self._create_onion_model(df),
                'security_overview': self._create_security_overview_charts(df),
                'temporal_analysis': self._create_temporal_charts(df),
                'user_activity': self._create_user_activity_charts(df),
                'door_analysis': self._create_door_analysis_charts(df),
                'risk_dashboard': self._create_risk_dashboard(df),
                'anomaly_visualization': self._create_anomaly_charts(df),
                'compliance_metrics': self._create_compliance_charts(df)
            }
            
            return charts
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {e}")
            return self._empty_charts()
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for chart generation"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['is_business_hours'] = (df['hour'] >= 8) & (df['hour'] <= 18)
        df['month'] = df['timestamp'].dt.month
        df['week'] = df['timestamp'].dt.isocalendar().week
        return df
    
    def _create_onion_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create security onion model visualization"""
        
        # Define security layers (from outside to inside)
        layers = [
            {'name': 'Perimeter', 'doors': ['DOOR001'], 'color': '#ff7f0e', 'radius': 100},
            {'name': 'General Access', 'doors': ['DOOR004'], 'color': '#2ca02c', 'radius': 80},
            {'name': 'Restricted', 'doors': ['DOOR003'], 'color': '#ff7f0e', 'radius': 60},
            {'name': 'Critical', 'doors': ['DOOR002', 'DOOR005'], 'color': '#d62728', 'radius': 40},
            {'name': 'Core', 'doors': [], 'color': '#1f77b4', 'radius': 20}
        ]
        
        # Calculate metrics for each layer
        layer_metrics = []
        for layer in layers:
            if layer['doors']:
                layer_data = df[df['door_id'].isin(layer['doors'])]
                metrics = {
                    'name': layer['name'],
                    'total_events': len(layer_data),
                    'success_rate': (layer_data['access_result'] == 'Granted').mean() * 100 if len(layer_data) > 0 else 0,
                    'unique_users': layer_data['person_id'].nunique() if len(layer_data) > 0 else 0,
                    'failed_attempts': len(layer_data[layer_data['access_result'] == 'Denied']),
                    'doors': layer['doors'],
                    'color': layer['color'],
                    'radius': layer['radius']
                }
            else:
                metrics = {
                    'name': layer['name'],
                    'total_events': 0,
                    'success_rate': 100,
                    'unique_users': 0,
                    'failed_attempts': 0,
                    'doors': [],
                    'color': layer['color'],
                    'radius': layer['radius']
                }
            layer_metrics.append(metrics)
        
        # Create onion chart
        onion_chart = self._create_onion_visualization(layer_metrics)
        
        # Create layer breakdown chart
        layer_breakdown = self._create_layer_breakdown_chart(layer_metrics)
        
        return {
            'onion_model': onion_chart,
            'layer_breakdown': layer_breakdown,
            'layer_metrics': layer_metrics,
            'security_score': self._calculate_onion_security_score(layer_metrics)
        }
    
    def _create_onion_visualization(self, layer_metrics: List[Dict]) -> go.Figure:
        """Create the actual onion model visualization"""
        
        fig = go.Figure()
        
        # Add concentric circles for each layer
        for i, layer in enumerate(layer_metrics):
            # Calculate opacity based on risk (lower success rate = higher opacity)
            opacity = 0.3 + (0.4 * (1 - layer['success_rate'] / 100))
            
            # Add circle
            theta = np.linspace(0, 2 * np.pi, 100)
            x = layer['radius'] * np.cos(theta)
            y = layer['radius'] * np.sin(theta)
            
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                fill='tonext' if i > 0 else 'toself',
                fillcolor=f"rgba{tuple(list(self._hex_to_rgb(layer['color'])) + [opacity])}",
                line=dict(color=layer['color'], width=2),
                name=layer['name'],
                hovertemplate=(
                    f"<b>{layer['name']} Layer</b><br>"
                    f"Events: {layer['total_events']}<br>"
                    f"Success Rate: {layer['success_rate']:.1f}%<br>"
                    f"Unique Users: {layer['unique_users']}<br>"
                    f"Failed Attempts: {layer['failed_attempts']}"
                    "<extra></extra>"
                )
            ))
            
            # Add layer label
            fig.add_annotation(
                x=0, y=layer['radius'] - 10,
                text=f"<b>{layer['name']}</b>",
                showarrow=False,
                font=dict(size=10, color="white"),
                bgcolor=layer['color'],
                bordercolor="white",
                borderwidth=1
            )
        
        # Customize layout
        fig.update_layout(
            title="Security Onion Model - Access Control Layers",
            xaxis=dict(
                range=[-120, 120],
                showgrid=False,
                showticklabels=False,
                zeroline=False
            ),
            yaxis=dict(
                range=[-120, 120],
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                scaleanchor="x",
                scaleratio=1
            ),
            showlegend=True,
            legend=dict(x=1.05, y=1),
            plot_bgcolor='white',
            height=500
        )
        
        return fig
    
    def _create_layer_breakdown_chart(self, layer_metrics: List[Dict]) -> go.Figure:
        """Create layer breakdown bar chart"""
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Events by Layer', 'Success Rates', 'User Access', 'Failed Attempts'],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        layers = [layer['name'] for layer in layer_metrics]
        colors = [layer['color'] for layer in layer_metrics]
        
        # Events by layer
        fig.add_trace(
            go.Bar(
                x=layers,
                y=[layer['total_events'] for layer in layer_metrics],
                marker_color=colors,
                name='Total Events'
            ),
            row=1, col=1
        )
        
        # Success rates
        fig.add_trace(
            go.Bar(
                x=layers,
                y=[layer['success_rate'] for layer in layer_metrics],
                marker_color=colors,
                name='Success Rate %'
            ),
            row=1, col=2
        )
        
        # Unique users
        fig.add_trace(
            go.Bar(
                x=layers,
                y=[layer['unique_users'] for layer in layer_metrics],
                marker_color=colors,
                name='Unique Users'
            ),
            row=2, col=1
        )
        
        # Failed attempts
        fig.add_trace(
            go.Bar(
                x=layers,
                y=[layer['failed_attempts'] for layer in layer_metrics],
                marker_color=['#d62728' if layer['failed_attempts'] > 0 else '#2ca02c' for layer in layer_metrics],
                name='Failed Attempts'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Security Layer Breakdown Analysis",
            showlegend=False,
            height=600
        )
        
        return fig
    
    def _create_security_overview_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create comprehensive security overview charts"""
        
        charts = {}
        
        # Access result pie chart
        result_counts = df['access_result'].value_counts()
        charts['access_results'] = go.Figure(data=[
            go.Pie(
                labels=result_counts.index,
                values=result_counts.values,
                hole=0.4,
                marker_colors=['#2ca02c', '#d62728'],
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        charts['access_results'].update_layout(
            title="Access Results Distribution",
            annotations=[dict(text='Access<br>Results', x=0.5, y=0.5, font_size=12, showarrow=False)]
        )
        
        # Daily success rate trend
        daily_success = df.groupby('date').agg({
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })['access_result']
        
        charts['success_trend'] = go.Figure()
        charts['success_trend'].add_trace(go.Scatter(
            x=daily_success.index,
            y=daily_success.values,
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6),
            name='Success Rate'
        ))
        charts['success_trend'].update_layout(
            title="Daily Access Success Rate Trend",
            xaxis_title="Date",
            yaxis_title="Success Rate (%)",
            yaxis=dict(range=[0, 100])
        )
        
        # Hourly activity heatmap
        hourly_activity = df.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hourly_activity = hourly_activity.reindex(day_order)
        
        charts['activity_heatmap'] = go.Figure(data=go.Heatmap(
            z=hourly_activity.values,
            x=hourly_activity.columns,
            y=hourly_activity.index,
            colorscale='Blues',
            hovertemplate='Day: %{y}<br>Hour: %{x}<br>Events: %{z}<extra></extra>'
        ))
        charts['activity_heatmap'].update_layout(
            title="Activity Heatmap - Day vs Hour",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week"
        )
        
        return charts
    
    def _create_temporal_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create temporal analysis charts"""
        
        charts = {}
        
        # Multi-metric time series
        daily_metrics = df.groupby('date').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'door_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        daily_metrics.columns = ['Total Events', 'Unique Users', 'Unique Doors', 'Success Rate']
        
        charts['time_series'] = make_subplots(
            rows=2, cols=2,
            subplot_titles=list(daily_metrics.columns),
            vertical_spacing=0.1
        )
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        for i, (col, color) in enumerate(zip(daily_metrics.columns, colors)):
            row = (i // 2) + 1
            col_pos = (i % 2) + 1
            
            charts['time_series'].add_trace(
                go.Scatter(
                    x=daily_metrics.index,
                    y=daily_metrics[col],
                    mode='lines+markers',
                    line=dict(color=color, width=2),
                    marker=dict(size=4),
                    name=col
                ),
                row=row, col=col_pos
            )
        
        charts['time_series'].update_layout(
            title="Temporal Analysis Dashboard",
            height=600,
            showlegend=False
        )
        
        # Peak hours analysis
        hourly_counts = df.groupby('hour')['event_id'].count()
        charts['peak_hours'] = go.Figure()
        
        # Color bars based on business hours
        colors = ['#ff7f0e' if hour < 8 or hour > 18 else '#1f77b4' for hour in hourly_counts.index]
        
        charts['peak_hours'].add_trace(go.Bar(
            x=hourly_counts.index,
            y=hourly_counts.values,
            marker_color=colors,
            hovertemplate='Hour: %{x}:00<br>Events: %{y}<extra></extra>'
        ))
        charts['peak_hours'].update_layout(
            title="Access Events by Hour of Day",
            xaxis_title="Hour",
            yaxis_title="Number of Events",
            xaxis=dict(tickmode='linear', tick0=0, dtick=2)
        )
        
        # Weekend vs Weekday comparison
        weekend_comparison = df.groupby(['is_weekend', 'hour'])['event_id'].count().unstack(level=0, fill_value=0)
        weekend_comparison.columns = ['Weekday', 'Weekend']
        
        charts['weekend_comparison'] = go.Figure()
        for col, color in zip(weekend_comparison.columns, ['#1f77b4', '#ff7f0e']):
            charts['weekend_comparison'].add_trace(go.Scatter(
                x=weekend_comparison.index,
                y=weekend_comparison[col],
                mode='lines+markers',
                name=col,
                line=dict(color=color, width=2)
            ))
        
        charts['weekend_comparison'].update_layout(
            title="Weekend vs Weekday Activity Patterns",
            xaxis_title="Hour of Day",
            yaxis_title="Average Events"
        )
        
        return charts
    
    def _create_user_activity_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create user activity analysis charts"""
        
        charts = {}
        
        # User activity distribution
        user_activity = df.groupby('person_id').agg({
            'event_id': 'count',
            'door_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        user_activity.columns = ['Total Events', 'Doors Accessed', 'Success Rate']
        
        # Activity distribution histogram
        charts['user_distribution'] = go.Figure()
        charts['user_distribution'].add_trace(go.Histogram(
            x=user_activity['Total Events'],
            nbinsx=20,
            marker_color='#1f77b4',
            opacity=0.7,
            hovertemplate='Events: %{x}<br>Users: %{y}<extra></extra>'
        ))
        charts['user_distribution'].update_layout(
            title="User Activity Distribution",
            xaxis_title="Number of Events per User",
            yaxis_title="Number of Users"
        )
        
        # Top users analysis
        top_users = user_activity.nlargest(20, 'Total Events')
        charts['top_users'] = go.Figure()
        
        # Color code by success rate
        colors = ['#d62728' if sr < 80 else '#ff7f0e' if sr < 95 else '#2ca02c' 
                  for sr in top_users['Success Rate']]
        
        charts['top_users'].add_trace(go.Bar(
            x=top_users.index,
            y=top_users['Total Events'],
            marker_color=colors,
            hovertemplate='User: %{x}<br>Events: %{y}<br>Success Rate: %{customdata:.1f}%<extra></extra>',
            customdata=top_users['Success Rate']
        ))
        charts['top_users'].update_layout(
            title="Top 20 Most Active Users",
            xaxis_title="User ID",
            yaxis_title="Total Events",
            xaxis=dict(tickangle=45)
        )
        
        # User behavior scatter plot
        charts['user_behavior'] = go.Figure()
        
        # Create size array for marker sizing
        sizes = np.clip(user_activity['Total Events'] / user_activity['Total Events'].max() * 50, 5, 50)
        
        charts['user_behavior'].add_trace(go.Scatter(
            x=user_activity['Doors Accessed'],
            y=user_activity['Success Rate'],
            mode='markers',
            marker=dict(
                size=sizes,
                color=user_activity['Total Events'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Total Events"),
                opacity=0.7
            ),
            text=user_activity.index,
            hovertemplate='User: %{text}<br>Doors: %{x}<br>Success Rate: %{y:.1f}%<br>Total Events: %{marker.color}<extra></extra>'
        ))
        charts['user_behavior'].update_layout(
            title="User Behavior Analysis - Door Diversity vs Success Rate",
            xaxis_title="Number of Different Doors Accessed",
            yaxis_title="Success Rate (%)"
        )
        
        return charts
    
    def _create_door_analysis_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create door analysis charts"""
        
        charts = {}
        
        # Door utilization
        door_stats = df.groupby('door_id').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        door_stats.columns = ['Total Events', 'Unique Users', 'Success Rate']
        
        # Door usage bar chart
        charts['door_usage'] = go.Figure()
        charts['door_usage'].add_trace(go.Bar(
            x=door_stats.index,
            y=door_stats['Total Events'],
            marker_color='#1f77b4',
            hovertemplate='Door: %{x}<br>Events: %{y}<br>Users: %{customdata}<extra></extra>',
            customdata=door_stats['Unique Users']
        ))
        charts['door_usage'].update_layout(
            title="Door Usage Analysis",
            xaxis_title="Door ID",
            yaxis_title="Total Events"
        )
        
        # Door security matrix
        charts['door_security'] = go.Figure()
        
        # Color code doors by success rate
        colors = ['#d62728' if sr < 80 else '#ff7f0e' if sr < 95 else '#2ca02c' 
                  for sr in door_stats['Success Rate']]
        
        charts['door_security'].add_trace(go.Scatter(
            x=door_stats['Total Events'],
            y=door_stats['Success Rate'],
            mode='markers+text',
            marker=dict(
                size=door_stats['Unique Users'] * 2,
                color=colors,
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=door_stats.index,
            textposition='middle center',
            hovertemplate='Door: %{text}<br>Events: %{x}<br>Success Rate: %{y:.1f}%<br>Unique Users: %{marker.size}<extra></extra>'
        ))
        charts['door_security'].update_layout(
            title="Door Security Analysis - Usage vs Success Rate",
            xaxis_title="Total Events",
            yaxis_title="Success Rate (%)"
        )
        
        # Failed attempts by door
        failed_by_door = df[df['access_result'] == 'Denied'].groupby('door_id').size()
        if len(failed_by_door) > 0:
            charts['door_failures'] = go.Figure()
            charts['door_failures'].add_trace(go.Bar(
                x=failed_by_door.index,
                y=failed_by_door.values,
                marker_color='#d62728',
                hovertemplate='Door: %{x}<br>Failed Attempts: %{y}<extra></extra>'
            ))
            charts['door_failures'].update_layout(
                title="Failed Access Attempts by Door",
                xaxis_title="Door ID",
                yaxis_title="Failed Attempts"
            )
        
        return charts
    
    def _create_risk_dashboard(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create risk assessment dashboard"""
        
        charts = {}
        
        # Risk indicators gauge chart
        total_events = len(df)
        failed_events = len(df[df['access_result'] == 'Denied'])
        after_hours_events = len(df[~df['is_business_hours']])
        weekend_events = len(df[df['is_weekend']])
        
        failure_rate = (failed_events / total_events) * 100 if total_events > 0 else 0
        after_hours_rate = (after_hours_events / total_events) * 100 if total_events > 0 else 0
        weekend_rate = (weekend_events / total_events) * 100 if total_events > 0 else 0
        
        # Overall risk score calculation
        risk_score = min(100, failure_rate * 2 + after_hours_rate * 0.5 + weekend_rate * 0.3)
        
        charts['risk_gauge'] = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Risk Score"},
            delta={'reference': 20},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "yellow"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        # Risk factors breakdown
        risk_factors = {
            'Failure Rate': failure_rate,
            'After Hours Activity': after_hours_rate,
            'Weekend Activity': weekend_rate
        }
        
        charts['risk_breakdown'] = go.Figure()
        colors = ['#d62728', '#ff7f0e', '#1f77b4']
        
        for i, (factor, value) in enumerate(risk_factors.items()):
            charts['risk_breakdown'].add_trace(go.Bar(
                x=[factor],
                y=[value],
                marker_color=colors[i],
                name=factor
            ))
        
        charts['risk_breakdown'].update_layout(
            title="Risk Factors Breakdown",
            yaxis_title="Percentage (%)",
            showlegend=False
        )
        
        # Time-based risk analysis
        daily_risk = df.groupby('date').agg({
            'access_result': lambda x: (x == 'Denied').mean() * 100,
            'is_business_hours': lambda x: (~x).mean() * 100
        })
        daily_risk.columns = ['Failure Rate', 'After Hours Rate']
        
        charts['risk_timeline'] = go.Figure()
        for col, color in zip(daily_risk.columns, ['#d62728', '#ff7f0e']):
            charts['risk_timeline'].add_trace(go.Scatter(
                x=daily_risk.index,
                y=daily_risk[col],
                mode='lines+markers',
                name=col,
                line=dict(color=color, width=2)
            ))
        
        charts['risk_timeline'].update_layout(
            title="Daily Risk Trends",
            xaxis_title="Date",
            yaxis_title="Risk Percentage (%)"
        )
        
        return charts
    
    def _create_anomaly_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create anomaly visualization charts"""
        
        charts = {}
        
        # Anomaly detection using statistical methods
        daily_volumes = df.groupby('date')['event_id'].count()
        
        if len(daily_volumes) > 3:
            # Calculate z-scores for anomaly detection
            mean_volume = daily_volumes.mean()
            std_volume = daily_volumes.std()
            z_scores = abs((daily_volumes - mean_volume) / std_volume)
            anomalies = daily_volumes[z_scores > 2]  # 2 standard deviations
            
            charts['volume_anomalies'] = go.Figure()
            
            # Normal days
            normal_days = daily_volumes[z_scores <= 2]
            charts['volume_anomalies'].add_trace(go.Scatter(
                x=normal_days.index,
                y=normal_days.values,
                mode='lines+markers',
                name='Normal Activity',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            ))
            
            # Anomalous days
            if len(anomalies) > 0:
                charts['volume_anomalies'].add_trace(go.Scatter(
                    x=anomalies.index,
                    y=anomalies.values,
                    mode='markers',
                    name='Anomalies',
                    marker=dict(
                        size=12,
                        color='#d62728',
                        symbol='x'
                    )
                ))
            
            # Add confidence bands
            upper_bound = mean_volume + 2 * std_volume
            lower_bound = mean_volume - 2 * std_volume
            
            charts['volume_anomalies'].add_trace(go.Scatter(
                x=daily_volumes.index,
                y=[upper_bound] * len(daily_volumes),
                mode='lines',
                name='Upper Threshold',
                line=dict(color='red', dash='dash'),
                showlegend=False
            ))
            
            charts['volume_anomalies'].add_trace(go.Scatter(
                x=daily_volumes.index,
                y=[lower_bound] * len(daily_volumes),
                mode='lines',
                name='Lower Threshold',
                line=dict(color='red', dash='dash'),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.1)',
                showlegend=False
            ))
            
            charts['volume_anomalies'].update_layout(
                title="Daily Volume Anomaly Detection",
                xaxis_title="Date",
                yaxis_title="Number of Events"
            )
        
        # User behavior anomalies
        user_activity = df.groupby('person_id')['event_id'].count()
        if len(user_activity) > 3:
            mean_activity = user_activity.mean()
            std_activity = user_activity.std()
            z_scores = abs((user_activity - mean_activity) / std_activity)
            anomalous_users = user_activity[z_scores > 2.5]
            
            if len(anomalous_users) > 0:
                charts['user_anomalies'] = go.Figure()
                charts['user_anomalies'].add_trace(go.Bar(
                    x=anomalous_users.index,
                    y=anomalous_users.values,
                    marker_color='#d62728',
                    hovertemplate='User: %{x}<br>Events: %{y}<br>Z-score: %{customdata:.2f}<extra></extra>',
                    customdata=z_scores[anomalous_users.index]
                ))
                charts['user_anomalies'].update_layout(
                    title="Anomalous User Activity",
                    xaxis_title="User ID",
                    yaxis_title="Number of Events",
                    xaxis=dict(tickangle=45)
                )
        
        return charts
    
    def _create_compliance_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create compliance monitoring charts"""
        
        charts = {}
        
        # Access compliance by time
        business_hours_compliance = df.groupby('date').agg({
            'is_business_hours': 'mean',
            'event_id': 'count'
        })
        business_hours_compliance['compliance_score'] = business_hours_compliance['is_business_hours'] * 100
        
        charts['time_compliance'] = go.Figure()
        charts['time_compliance'].add_trace(go.Scatter(
            x=business_hours_compliance.index,
            y=business_hours_compliance['compliance_score'],
            mode='lines+markers',
            name='Business Hours Compliance',
            line=dict(color='#2ca02c', width=2),
            fill='tonexty',
            fillcolor='rgba(44,160,44,0.1)'
        ))
        
        # Add compliance threshold line
        charts['time_compliance'].add_trace(go.Scatter(
            x=business_hours_compliance.index,
            y=[80] * len(business_hours_compliance),
            mode='lines',
            name='Compliance Threshold (80%)',
            line=dict(color='red', dash='dash')
        ))
        
        charts['time_compliance'].update_layout(
            title="Daily Business Hours Compliance",
            xaxis_title="Date",
            yaxis_title="Compliance Score (%)",
            yaxis=dict(range=[0, 100])
        )
        
        # Badge compliance
        if 'badge_status' in df.columns:
            badge_compliance = df.groupby('date').agg({
                'badge_status': lambda x: (x == 'Valid').mean() * 100
            })['badge_status']
            
            charts['badge_compliance'] = go.Figure()
            charts['badge_compliance'].add_trace(go.Scatter(
                x=badge_compliance.index,
                y=badge_compliance.values,
                mode='lines+markers',
                name='Badge Compliance',
                line=dict(color='#1f77b4', width=2)
            ))
            
            charts['badge_compliance'].update_layout(
                title="Daily Badge Compliance Rate",
                xaxis_title="Date",
                yaxis_title="Valid Badge Usage (%)",
                yaxis=dict(range=[0, 100])
            )
        
        # Overall compliance dashboard
        compliance_metrics = {
            'Access Success Rate': (df['access_result'] == 'Granted').mean() * 100,
            'Business Hours Compliance': df['is_business_hours'].mean() * 100,
            'Valid Badge Usage': (df['badge_status'] == 'Valid').mean() * 100 if 'badge_status' in df.columns else 100
        }
        
        charts['compliance_summary'] = go.Figure()
        
        colors = ['#2ca02c' if score >= 90 else '#ff7f0e' if score >= 80 else '#d62728' 
                  for score in compliance_metrics.values()]
        
        charts['compliance_summary'].add_trace(go.Bar(
            x=list(compliance_metrics.keys()),
            y=list(compliance_metrics.values()),
            marker_color=colors,
            hovertemplate='Metric: %{x}<br>Score: %{y:.1f}%<extra></extra>'
        ))
        
        charts['compliance_summary'].update_layout(
            title="Compliance Metrics Summary",
            yaxis_title="Compliance Score (%)",
            yaxis=dict(range=[0, 100])
        )
        
        return charts
    
    # Helper methods
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _calculate_onion_security_score(self, layer_metrics: List[Dict]) -> Dict[str, Any]:
        """Calculate overall security score for onion model"""
        
        # Weight layers by criticality (inner layers more important)
        weights = [1, 2, 3, 5, 8]  # Fibonacci-like weighting
        
        total_score = 0
        total_weight = 0
        
        for layer, weight in zip(layer_metrics, weights):
            if layer['total_events'] > 0:  # Only consider active layers
                layer_score = layer['success_rate']
                total_score += layer_score * weight
                total_weight += weight
        
        overall_score = total_score / total_weight if total_weight > 0 else 100
        
        # Determine security level
        if overall_score >= 95:
            security_level = 'Excellent'
        elif overall_score >= 90:
            security_level = 'Good'
        elif overall_score >= 80:
            security_level = 'Fair'
        else:
            security_level = 'Poor'
        
        return {
            'overall_score': overall_score,
            'security_level': security_level,
            'layer_weights': weights,
            'recommendations': self._generate_onion_recommendations(layer_metrics)
        }
    
    def _generate_onion_recommendations(self, layer_metrics: List[Dict]) -> List[str]:
        """Generate recommendations based on onion model analysis"""
        
        recommendations = []
        
        for layer in layer_metrics:
            if layer['success_rate'] < 90 and layer['total_events'] > 0:
                recommendations.append(
                    f"Review security controls for {layer['name']} layer "
                    f"(success rate: {layer['success_rate']:.1f}%)"
                )
            
            if layer['failed_attempts'] > 10:
                recommendations.append(
                    f"Investigate high failure rate in {layer['name']} layer "
                    f"({layer['failed_attempts']} failed attempts)"
                )
        
        if not recommendations:
            recommendations.append("Security posture appears good across all layers")
        
        return recommendations
    
    def _empty_charts(self) -> Dict[str, Any]:
        """Return empty charts structure"""
        return {
            'onion_model': {'onion_model': go.Figure(), 'layer_breakdown': go.Figure()},
            'security_overview': {},
            'temporal_analysis': {},
            'user_activity': {},
            'door_analysis': {},
            'risk_dashboard': {},
            'anomaly_visualization': {},
            'compliance_metrics': {}
        }

# Factory function
def create_charts_generator() -> SecurityChartsGenerator:
    """Create security charts generator instance"""
    return SecurityChartsGenerator()

# Export
__all__ = ['SecurityChartsGenerator', 'create_charts_generator']
