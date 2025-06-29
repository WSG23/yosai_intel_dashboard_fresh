#!/usr/bin/env python3
"""
Settings Persistence Service - Integrated with existing database system
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import asdict

# Use existing database manager
from config.database_manager import DatabaseManager
from components.ui_settings import UserSettings, AdminSettings

logger = logging.getLogger(__name__)

class SettingsPersistenceService:
    """Service for persisting settings - uses existing database patterns"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def save_user_settings(self, user_id: str, settings: UserSettings) -> bool:
        """Save user settings using existing database patterns"""
        try:
            settings_json = json.dumps(asdict(settings))
            
            # Use the same pattern as existing database operations
            if self.db.config.type == "mock":
                # For development/testing
                logger.info(f"Mock save: User settings for {user_id}")
                return True
            
            query = """
            INSERT INTO user_settings (user_id, settings_data, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                settings_data = EXCLUDED.settings_data,
                updated_at = EXCLUDED.updated_at
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        user_id, 
                        settings_json, 
                        datetime.now(timezone.utc)
                    ))
                    conn.commit()
            
            logger.info(f"User settings saved for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user settings: {e}")
            return False
    
    def load_user_settings(self, user_id: str) -> UserSettings:
        """Load user settings using existing database patterns"""
        try:
            if self.db.config.type == "mock":
                # Return defaults for development
                return UserSettings()
            
            query = "SELECT settings_data FROM user_settings WHERE user_id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
            
            if result:
                settings_data = json.loads(result[0])
                return UserSettings(**settings_data)
            else:
                return UserSettings()  # Return defaults
                
        except Exception as e:
            logger.error(f"Failed to load user settings: {e}")
            return UserSettings()
    
    def save_admin_settings(self, settings: AdminSettings) -> bool:
        """Save admin settings using existing patterns"""
        try:
            settings_json = json.dumps(asdict(settings))
            
            if self.db.config.type == "mock":
                # For development/testing
                logger.info("Mock save: Admin settings")
                return True
            
            query = """
            INSERT INTO admin_settings (settings_name, settings_data, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (settings_name)
            DO UPDATE SET
                settings_data = EXCLUDED.settings_data,
                updated_at = EXCLUDED.updated_at
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        "main_config",
                        settings_json,
                        datetime.now(timezone.utc)
                    ))
                    conn.commit()
            
            logger.info("Admin settings saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save admin settings: {e}")
            return False
    
    def load_admin_settings(self) -> AdminSettings:
        """Load admin settings using existing patterns"""
        try:
            if self.db.config.type == "mock":
                return AdminSettings()
            
            query = "SELECT settings_data FROM admin_settings WHERE settings_name = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, ("main_config",))
                    result = cursor.fetchone()
            
            if result:
                settings_data = json.loads(result[0])
                return AdminSettings(**settings_data)
            else:
                return AdminSettings()
                
        except Exception as e:
            logger.error(f"Failed to load admin settings: {e}")
            return AdminSettings()

# Export service class
__all__ = ["SettingsPersistenceService"]
