#!/usr/bin/env python3
"""
User & Device Metadata Enhancement Module
Rich metadata management for access control systems
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from config.app_config import UploadConfig
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import bleach

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _sanitize(text: str) -> str:
    """Remove potentially unsafe HTML from user-provided text."""
    return bleach.clean(str(text), tags=[], attributes={}, strip=True)

def show_metadata_enhancement():
    st.header("👥 User & Device Metadata Enhancement")
    st.markdown("### Enrich your access control system with detailed user profiles and device metadata")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👤 User Profiles", "🚪 Device Enhancement", "🔗 Relationships", "📊 Metadata Analytics"])
    
    with tab1:
        show_user_profiles()
    
    with tab2:
        show_device_enhancement()
    
    with tab3:
        show_user_device_relationships()
    
    with tab4:
        show_metadata_analytics()

def show_user_profiles():
    st.subheader("👤 User Profile Management")
    
    # Load current users from Enhanced Security Demo
    try:
        parquet_path = Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            unique_employees = df['Employee Code'].unique()
            unique_cards = df['Access Card'].unique()
            
            st.info(f"Found {len(unique_employees)} employees and {len(unique_cards)} access cards in your data")
            
            # Load existing user profiles
            user_profiles = load_user_profiles()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### 🔍 Select Employee")
                selected_employee = st.selectbox("Employee Code:", unique_employees)
                
                # Add new user button
                if st.button("➕ Create New User Profile", help="Create New User Profile"):
                    st.session_state.show_user_form = True
                    st.session_state.edit_user = selected_employee
            
            with col2:
                if selected_employee:
                    show_user_profile_form(selected_employee, user_profiles, unique_cards)
            
            # Show user profiles summary
            st.subheader("📋 User Profiles Summary")
            if user_profiles:
                profiles_df = pd.DataFrame.from_dict(user_profiles, orient='index')
                st.dataframe(profiles_df, use_container_width=True)
                
                # Download user profiles
                if st.button("💾 Export User Profiles", help="Export User Profiles"):
                    csv = profiles_df.to_csv(index=True)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"user_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No user profiles created yet. Create profiles to enhance your access control metadata.")
                
        else:
            st.warning("Enhanced Security Demo data not found. Please ensure the data is loaded.")
            
    except Exception as e:
        st.error(f"Error loading user data: {e}")

def show_user_profile_form(employee_code, user_profiles, available_cards):
    st.markdown(f"#### 👤 Profile for {_sanitize(employee_code)}")
    
    # Load existing profile or create new
    existing_profile = user_profiles.get(employee_code, {})
    
    with st.form(f"user_profile_{employee_code}"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=existing_profile.get('full_name', ''))
            department = st.selectbox(
                "Department",
                ["Engineering", "Finance", "HR", "Marketing", "Operations", "Security", "Executive", "IT", "Legal", "Other"],
                index=["Engineering", "Finance", "HR", "Marketing", "Operations", "Security", "Executive", "IT", "Legal", "Other"].index(existing_profile.get('department', 'Other'))
            )
            job_title = st.text_input("Job Title", value=existing_profile.get('job_title', ''))
            email = st.text_input("Email", value=existing_profile.get('email', ''))
            
        with col2:
            clearance_level = st.selectbox(
                "Security Clearance",
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                index=existing_profile.get('clearance_level', 5) - 1
            )
            
            employee_type = st.selectbox(
                "Employee Type",
                ["Full-time", "Part-time", "Contractor", "Temporary", "Intern"],
                index=["Full-time", "Part-time", "Contractor", "Temporary", "Intern"].index(existing_profile.get('employee_type', 'Full-time'))
            )
            
            assigned_card = st.selectbox(
                "Assigned Access Card",
                ["None"] + list(available_cards),
                index=0 if existing_profile.get('assigned_card') not in available_cards else list(available_cards).index(existing_profile.get('assigned_card')) + 1
            )
            
            manager = st.text_input("Manager", value=existing_profile.get('manager', ''))
        
        # Additional metadata
        st.markdown("##### 📝 Additional Information")
        col3, col4 = st.columns(2)
        
        with col3:
            start_date = st.date_input("Start Date", value=datetime.now().date())
            phone = st.text_input("Phone", value=existing_profile.get('phone', ''))
            
        with col4:
            office_location = st.text_input("Office Location", value=existing_profile.get('office_location', ''))
            notes = st.text_area("Notes", value=existing_profile.get('notes', ''))
        
        # Submit button
        if st.form_submit_button("💾 Save User Profile", help="Save User Profile"):
            new_profile = {
                'full_name': full_name,
                'department': department,
                'job_title': job_title,
                'email': email,
                'clearance_level': clearance_level,
                'employee_type': employee_type,
                'assigned_card': assigned_card if assigned_card != "None" else None,
                'manager': manager,
                'start_date': start_date.isoformat(),
                'phone': phone,
                'office_location': office_location,
                'notes': notes,
                'last_updated': datetime.now().isoformat()
            }
            
            save_user_profile(employee_code, new_profile)
            st.success(
                f"✅ Profile saved for {_sanitize(employee_code)} ({_sanitize(full_name)})"
            )
            st.experimental_rerun()

def show_device_enhancement():
    st.subheader("🚪 Device Metadata Enhancement")
    
    try:
        from services.device_learning_service import DeviceLearningService
        device_service = DeviceLearningService()
        mappings = device_service.learned_mappings
        
        if not mappings:
            st.warning("No device mappings found")
            return
        
        # Select mapping to enhance
        enhanced_mappings = [(k, v) for k, v in mappings.items() if 'Enhanced_Security_Demo' in str(v.get('filename', ''))]
        
        if enhanced_mappings:
            mapping_key, mapping_data = enhanced_mappings[0]
            device_mappings = mapping_data.get('device_mappings', {})
            
            st.info(
                f"Enhancing devices from: {_sanitize(mapping_data.get('filename', 'Unknown'))} ({len(device_mappings)} devices)"
            )
            
            # Load enhanced device metadata
            enhanced_devices = load_enhanced_device_metadata()
            
            # Device selection
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### 🔍 Select Device")
                device_list = list(device_mappings.keys())
                selected_device = st.selectbox("Device:", device_list)
                
                if st.button(
                    "🔄 Refresh Device List", help="Refresh Device List"
                ):
                    st.experimental_rerun()
            
            with col2:
                if selected_device:
                    show_device_enhancement_form(selected_device, device_mappings[selected_device], enhanced_devices)
            
            # Enhanced devices summary
            st.subheader("📋 Enhanced Device Summary")
            if enhanced_devices:
                devices_df = pd.DataFrame.from_dict(enhanced_devices, orient='index')
                st.dataframe(devices_df, use_container_width=True)
                
                # Download enhanced device data
                if st.button(
                    "💾 Export Enhanced Device Data",
                    help="Export Enhanced Device Data",
                ):
                    csv = devices_df.to_csv(index=True)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"enhanced_devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No enhanced device metadata created yet.")
                
        else:
            st.warning("No Enhanced Security Demo device mappings found")
            
    except Exception as e:
        st.error(f"Device enhancement error: {e}")

def show_device_enhancement_form(device_name, original_mapping, enhanced_devices):
    st.markdown(f"#### 🚪 Enhanced Metadata for {_sanitize(device_name)}")
    
    # Show original mapping info
    with st.expander("📋 Original Device Mapping", expanded=False):
        st.json(original_mapping)
    
    # Load existing enhanced metadata
    existing_enhanced = enhanced_devices.get(device_name, {})
    
    with st.form(f"device_enhancement_{device_name}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏢 Physical Information")
            building = st.text_input("Building", value=existing_enhanced.get('building', 'Main Building'))
            floor_name = st.text_input("Floor Name", value=existing_enhanced.get('floor_name', f"Floor {original_mapping.get('floor_number', 'Unknown')}"))
            zone = st.text_input("Zone/Area", value=existing_enhanced.get('zone', ''))
            room_number = st.text_input("Room Number", value=existing_enhanced.get('room_number', ''))
            
            st.markdown("##### 🔧 Technical Details")
            device_type = st.selectbox(
                "Device Type",
                ["Card Reader", "Biometric Scanner", "Keypad", "Motion Sensor", "Security Camera", "Intercom", "Turnstile", "Gate", "Other"],
                index=["Card Reader", "Biometric Scanner", "Keypad", "Motion Sensor", "Security Camera", "Intercom", "Turnstile", "Gate", "Other"].index(existing_enhanced.get('device_type', 'Card Reader'))
            )
            
            manufacturer = st.text_input("Manufacturer", value=existing_enhanced.get('manufacturer', ''))
            model = st.text_input("Model", value=existing_enhanced.get('model', ''))
            serial_number = st.text_input("Serial Number", value=existing_enhanced.get('serial_number', ''))
        
        with col2:
            st.markdown("##### 🛡️ Security & Access")
            
            # Use original security level as default
            enhanced_security_level = st.slider(
                "Enhanced Security Level",
                min_value=1, max_value=10,
                value=existing_enhanced.get('enhanced_security_level', original_mapping.get('security_level', 5))
            )
            
            access_hours = st.selectbox(
                "Access Hours",
                ["24/7", "Business Hours", "Restricted Hours", "Emergency Only"],
                index=["24/7", "Business Hours", "Restricted Hours", "Emergency Only"].index(existing_enhanced.get('access_hours', '24/7'))
            )
            
            requires_escort = st.checkbox("Requires Escort", value=existing_enhanced.get('requires_escort', False))
            dual_auth_required = st.checkbox("Dual Authentication Required", value=existing_enhanced.get('dual_auth_required', False))
            
            st.markdown("##### 📊 Monitoring")
            camera_coverage = st.checkbox("Camera Coverage", value=existing_enhanced.get('camera_coverage', True))
            logging_enabled = st.checkbox("Access Logging", value=existing_enhanced.get('logging_enabled', True))
            alert_enabled = st.checkbox("Security Alerts", value=existing_enhanced.get('alert_enabled', False))
            
        # Additional metadata
        st.markdown("##### 📝 Additional Information")
        col3, col4 = st.columns(2)
        
        with col3:
            installation_date = st.date_input("Installation Date", value=datetime.now().date())
            last_maintenance = st.date_input("Last Maintenance", value=datetime.now().date())
            
        with col4:
            responsible_person = st.text_input("Responsible Person", value=existing_enhanced.get('responsible_person', ''))
            notes = st.text_area("Notes", value=existing_enhanced.get('notes', ''))
        
        # Submit button
        if st.form_submit_button("💾 Save Enhanced Device Data"):
            enhanced_metadata = {
                'device_name': device_name,
                'building': building,
                'floor_name': floor_name,
                'zone': zone,
                'room_number': room_number,
                'device_type': device_type,
                'manufacturer': manufacturer,
                'model': model,
                'serial_number': serial_number,
                'enhanced_security_level': enhanced_security_level,
                'access_hours': access_hours,
                'requires_escort': requires_escort,
                'dual_auth_required': dual_auth_required,
                'camera_coverage': camera_coverage,
                'logging_enabled': logging_enabled,
                'alert_enabled': alert_enabled,
                'installation_date': installation_date.isoformat(),
                'last_maintenance': last_maintenance.isoformat(),
                'responsible_person': responsible_person,
                'notes': notes,
                'original_mapping': original_mapping,
                'last_updated': datetime.now().isoformat()
            }
            
            save_enhanced_device_metadata(device_name, enhanced_metadata)
            st.success(f"✅ Enhanced metadata saved for {_sanitize(device_name)}")
            st.experimental_rerun()

def show_user_device_relationships():
    st.subheader("🔗 User-Device Relationships & Permissions")
    
    # Load data
    user_profiles = load_user_profiles()
    enhanced_devices = load_enhanced_device_metadata()
    
    if not user_profiles:
        st.warning("Create user profiles first to manage relationships")
        return
    
    if not enhanced_devices:
        st.warning("Enhance device metadata first to manage relationships")
        return
    
    # Access permissions matrix
    st.markdown("#### 🔐 Access Permissions Matrix")
    
    # Create permissions matrix
    users = list(user_profiles.keys())
    devices = list(enhanced_devices.keys())
    
    if users and devices:
        # Load existing permissions
        permissions = load_access_permissions()
        
        # Create interactive permissions grid
        st.markdown("##### Set Access Permissions")
        
        with st.expander("🔧 Bulk Permission Settings", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                bulk_user = st.selectbox("Select User for Bulk:", users)
            with col2:
                bulk_permission = st.selectbox("Permission Level:", ["Denied", "Granted", "Conditional"])
            with col3:
                if st.button("Apply to All Devices", help="Apply to All Devices"):
                    for device in devices:
                        if bulk_user not in permissions:
                            permissions[bulk_user] = {}
                        permissions[bulk_user][device] = bulk_permission
                    save_access_permissions(permissions)
                    st.success(
                        f"Applied {_sanitize(bulk_permission)} permission for {_sanitize(bulk_user)} to all devices"
                    )
                    st.experimental_rerun()
        
        # Individual permissions
        selected_user = st.selectbox("Select User:", users)
        
        if selected_user:
            user_info = user_profiles[selected_user]
            st.info(
                f"Managing permissions for: {_sanitize(user_info.get('full_name', selected_user))} ({_sanitize(user_info.get('department', 'Unknown Dept'))})"
            )
            
            user_permissions = permissions.get(selected_user, {})
            
            # Show permissions in columns
            cols = st.columns(3)
            
            for i, device in enumerate(devices):
                with cols[i % 3]:
                    device_info = enhanced_devices[device]
                    current_permission = user_permissions.get(device, "Not Set")
                    
                    st.markdown(f"**{_sanitize(device)}**")
                    st.caption(
                        f"Security Level: {device_info.get('enhanced_security_level', 'N/A')}"
                    )
                    
                    new_permission = st.selectbox(
                        "Permission:",
                        ["Not Set", "Denied", "Granted", "Conditional"],
                        index=["Not Set", "Denied", "Granted", "Conditional"].index(current_permission),
                        key=f"perm_{selected_user}_{device}"
                    )
                    
                    if new_permission != current_permission:
                        if selected_user not in permissions:
                            permissions[selected_user] = {}
                        permissions[selected_user][device] = new_permission
                        save_access_permissions(permissions)
                        st.success(f"Updated: {_sanitize(new_permission)}")
    
    # Permissions analytics
    st.markdown("#### 📊 Permissions Analytics")
    
    if 'permissions' in locals() and permissions:
        # Create summary dataframe
        permission_data = []
        for user, user_perms in permissions.items():
            user_info = user_profiles.get(user, {})
            for device, permission in user_perms.items():
                device_info = enhanced_devices.get(device, {})
                permission_data.append({
                    'User': user,
                    'Full Name': user_info.get('full_name', 'Unknown'),
                    'Department': user_info.get('department', 'Unknown'),
                    'Clearance': user_info.get('clearance_level', 0),
                    'Device': device,
                    'Device Type': device_info.get('device_type', 'Unknown'),
                    'Security Level': device_info.get('enhanced_security_level', 0),
                    'Permission': permission
                })
        
        if permission_data:
            perms_df = pd.DataFrame(permission_data)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_permissions = len(perms_df)
                st.metric("Total Permissions", total_permissions)
            
            with col2:
                granted_count = len(perms_df[perms_df['Permission'] == 'Granted'])
                st.metric("Granted", granted_count)
            
            with col3:
                denied_count = len(perms_df[perms_df['Permission'] == 'Denied'])
                st.metric("Denied", denied_count)
            
            with col4:
                conditional_count = len(perms_df[perms_df['Permission'] == 'Conditional'])
                st.metric("Conditional", conditional_count)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Permissions by department
                dept_perms = perms_df.groupby(['Department', 'Permission']).size().reset_index(name='Count')
                fig = px.bar(
                    dept_perms, 
                    x='Department', 
                    y='Count', 
                    color='Permission',
                    title="Permissions by Department"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Security level vs clearance analysis
                security_clearance = perms_df[perms_df['Permission'] == 'Granted'].copy()
                if not security_clearance.empty:
                    fig = px.scatter(
                        security_clearance,
                        x='Clearance',
                        y='Security Level',
                        color='Department',
                        title="Clearance vs Security Level (Granted Access)",
                        hover_data=['User', 'Device']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Detailed permissions table
            st.markdown("##### 📋 Detailed Permissions")
            st.dataframe(perms_df, use_container_width=True)

def show_metadata_analytics():
    st.subheader("📊 Metadata Analytics Dashboard")
    
    # Load all metadata
    user_profiles = load_user_profiles()
    enhanced_devices = load_enhanced_device_metadata()
    permissions = load_access_permissions()
    
    if not user_profiles and not enhanced_devices:
        st.info("Create user profiles and enhance device metadata to see analytics")
        return
    
    # User analytics
    if user_profiles:
        st.markdown("#### 👥 User Analytics")
        
        users_df = pd.DataFrame.from_dict(user_profiles, orient='index')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Department distribution
            dept_counts = users_df['department'].value_counts()
            fig = px.pie(
                values=dept_counts.values,
                names=dept_counts.index,
                title="Users by Department"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Clearance level distribution
            clearance_counts = users_df['clearance_level'].value_counts().sort_index()
            fig = px.bar(
                x=clearance_counts.index,
                y=clearance_counts.values,
                title="Users by Clearance Level",
                labels={'x': 'Clearance Level', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Employee type distribution
            type_counts = users_df['employee_type'].value_counts()
            fig = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                orientation='h',
                title="Users by Employee Type"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Device analytics
    if enhanced_devices:
        st.markdown("#### 🚪 Device Analytics")
        
        devices_df = pd.DataFrame.from_dict(enhanced_devices, orient='index')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Device type distribution
            type_counts = devices_df['device_type'].value_counts()
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Devices by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Security level distribution
            security_counts = devices_df['enhanced_security_level'].value_counts().sort_index()
            fig = px.bar(
                x=security_counts.index,
                y=security_counts.values,
                title="Devices by Security Level",
                labels={'x': 'Security Level', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Access hours distribution
            hours_counts = devices_df['access_hours'].value_counts()
            fig = px.bar(
                x=hours_counts.values,
                y=hours_counts.index,
                orientation='h',
                title="Devices by Access Hours"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Combined analytics
    if user_profiles and enhanced_devices and permissions:
        st.markdown("#### 🔗 Combined System Analytics")
        
        # Security compliance analysis
        st.markdown("##### 🛡️ Security Compliance Analysis")
        
        compliance_issues = []
        
        # Check for clearance vs security level mismatches
        for user, user_perms in permissions.items():
            user_info = user_profiles.get(user, {})
            user_clearance = user_info.get('clearance_level', 0)
            
            for device, permission in user_perms.items():
                if permission == 'Granted':
                    device_info = enhanced_devices.get(device, {})
                    device_security = device_info.get('enhanced_security_level', 0)
                    
                    if user_clearance < device_security:
                        compliance_issues.append({
                            'Issue Type': 'Clearance Mismatch',
                            'User': user,
                            'User Clearance': user_clearance,
                            'Device': device,
                            'Device Security': device_security,
                            'Risk Level': 'High' if (device_security - user_clearance) > 2 else 'Medium'
                        })
        
        if compliance_issues:
            st.warning(f"⚠️ Found {len(compliance_issues)} potential security compliance issues")
            issues_df = pd.DataFrame(compliance_issues)
            st.dataframe(issues_df, use_container_width=True)
        else:
            st.success("✅ No security compliance issues detected")

# Data persistence functions
def load_user_profiles():
    """Load user profiles from file"""
    profiles_file = Path("simple_ui/user_profiles.json")
    if profiles_file.exists():
        try:
            with open(profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_profile(employee_code, profile_data):
    """Save user profile to file"""
    profiles = load_user_profiles()
    profiles[employee_code] = profile_data
    
    profiles_file = Path("simple_ui/user_profiles.json")
    profiles_file.parent.mkdir(exist_ok=True)
    
    with open(profiles_file, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2)

def load_enhanced_device_metadata():
    """Load enhanced device metadata from file"""
    devices_file = Path("simple_ui/enhanced_devices.json")
    if devices_file.exists():
        try:
            with open(devices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_enhanced_device_metadata(device_name, metadata):
    """Save enhanced device metadata to file"""
    devices = load_enhanced_device_metadata()
    devices[device_name] = metadata
    
    devices_file = Path("simple_ui/enhanced_devices.json")
    devices_file.parent.mkdir(exist_ok=True)
    
    with open(devices_file, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2)

def load_access_permissions():
    """Load access permissions from file"""
    perms_file = Path("simple_ui/access_permissions.json")
    if perms_file.exists():
        try:
            with open(perms_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_access_permissions(permissions):
    """Save access permissions to file"""
    perms_file = Path("simple_ui/access_permissions.json")
    perms_file.parent.mkdir(exist_ok=True)
    
    with open(perms_file, 'w', encoding='utf-8') as f:
        json.dump(permissions, f, indent=2)
