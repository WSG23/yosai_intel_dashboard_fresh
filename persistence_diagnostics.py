#!/usr/bin/env python3
"""
Device Mapping Persistence Diagnostics
Verify that device mappings are actually being saved and loaded from filesystem
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_storage_directory():
    """Check if the storage directory exists and what's in it."""
    print("🔍 CHECKING STORAGE DIRECTORY")
    print("=" * 50)
    
    storage_dir = Path("data/device_learning")
    print(f"📂 Storage directory: {storage_dir.absolute()}")
    print(f"📂 Directory exists: {storage_dir.exists()}")
    
    if storage_dir.exists():
        mapping_files = list(storage_dir.glob("mapping_*.json"))
        print(f"📄 Found {len(mapping_files)} mapping files")
        
        for i, file_path in enumerate(mapping_files):
            size = file_path.stat().st_size
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"   {i+1}. {file_path.name} ({size} bytes, modified: {modified})")
            
            # Show file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"      - Filename: {data.get('filename', 'N/A')}")
                    print(f"      - Device count: {data.get('device_count', 0)}")
                    print(f"      - Saved at: {data.get('saved_at', 'N/A')}")
                    
                    # Check both key structures
                    mappings = data.get('device_mappings', {}) or data.get('mappings', {})
                    if mappings:
                        devices = list(mappings.keys())[:3]
                        print(f"      - Sample devices: {devices}")
                    else:
                        print(f"      - ⚠️  No device mappings found!")
                        
            except Exception as e:
                print(f"      - ❌ Error reading file: {e}")
    else:
        print("📂 Creating storage directory...")
        storage_dir.mkdir(parents=True, exist_ok=True)
        print("📂 Directory created successfully")
    
    print()

def test_save_load_cycle():
    """Test a complete save/load cycle to prove persistence."""
    print("🧪 TESTING SAVE/LOAD CYCLE")
    print("=" * 50)
    
    try:
        # Import the service
        from services.device_learning_service import get_device_learning_service
        
        # Create test data
        test_df = pd.DataFrame({
            'door_id': ['test_lobby', 'test_office', 'test_server'],
            'timestamp': ['2024-01-01 10:00:00', '2024-01-01 10:30:00', '2024-01-01 11:00:00'],
            'user_id': ['user1', 'user2', 'user3']
        })
        
        test_filename = f"diagnostic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create test device mappings
        test_mappings = {
            'test_lobby': {
                'floor_number': 1,
                'security_level': 3,
                'device_name': 'Test Lobby',
                'is_entry': True,
                'is_exit': True,
                'confidence': 1.0,
                'source': 'diagnostic_test'
            },
            'test_office': {
                'floor_number': 2,
                'security_level': 7,
                'device_name': 'Test Office',
                'is_entry': True,
                'is_exit': False,
                'confidence': 1.0,
                'source': 'diagnostic_test'
            },
            'test_server': {
                'floor_number': -1,
                'security_level': 10,
                'device_name': 'Test Server Room',
                'is_entry': True,
                'is_exit': False,
                'confidence': 1.0,
                'source': 'diagnostic_test'
            }
        }
        
        learning_service = get_device_learning_service()
        
        print(f"📝 Step 1: Saving test mappings for '{test_filename}'...")
        save_result = learning_service.save_user_device_mappings(test_df, test_filename, test_mappings)
        print(f"📝 Save result: {save_result}")
        
        if save_result:
            print("✅ Save operation reported success")
            
            # Check if file was actually created
            storage_dir = Path("data/device_learning")
            mapping_files = list(storage_dir.glob("mapping_*.json"))
            
            print(f"📄 Files in storage after save: {len(mapping_files)}")
            
            # Find our file
            our_file = None
            for file_path in mapping_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('filename') == test_filename:
                            our_file = file_path
                            break
                except:
                    continue
            
            if our_file:
                print(f"✅ Found our saved file: {our_file.name}")
                print(f"📄 File size: {our_file.stat().st_size} bytes")
                
                # Show file contents
                with open(our_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    print(f"📄 File contents preview:")
                    print(f"   - Filename: {file_data.get('filename')}")
                    print(f"   - Fingerprint: {file_data.get('fingerprint')}")
                    print(f"   - Device count: {file_data.get('device_count')}")
                    
                    mappings = file_data.get('device_mappings', {}) or file_data.get('mappings', {})
                    print(f"   - Mappings found: {len(mappings)}")
                    for device, mapping in mappings.items():
                        print(f"     * {device}: floor={mapping.get('floor_number')}, security={mapping.get('security_level')}")
                
            else:
                print("❌ Could not find our saved file!")
                return False
            
            # Test retrieval
            print(f"\n📖 Step 2: Testing retrieval...")
            retrieved_mappings = learning_service.get_user_device_mappings(test_filename)
            
            if retrieved_mappings:
                print(f"✅ Retrieved {len(retrieved_mappings)} mappings")
                for device, mapping in retrieved_mappings.items():
                    print(f"   - {device}: {mapping.get('device_name')} (floor {mapping.get('floor_number')})")
                
                # Verify data integrity
                if len(retrieved_mappings) == len(test_mappings):
                    print("✅ Device count matches")
                else:
                    print(f"❌ Device count mismatch: saved {len(test_mappings)}, retrieved {len(retrieved_mappings)}")
                
                # Check specific values
                if 'test_lobby' in retrieved_mappings:
                    lobby_data = retrieved_mappings['test_lobby']
                    if lobby_data.get('floor_number') == 1 and lobby_data.get('security_level') == 3:
                        print("✅ Data integrity verified")
                    else:
                        print("❌ Data integrity failed")
                else:
                    print("❌ Expected device 'test_lobby' not found")
                
            else:
                print("❌ No mappings retrieved!")
                return False
            
            # Test persistence across service restart
            print(f"\n🔄 Step 3: Testing persistence across service restart...")
            
            # Create a new service instance (simulates app restart)
            from services.device_learning_service import DeviceLearningService
            new_service = DeviceLearningService()
            
            # Try to retrieve our data with the new service
            persistent_mappings = new_service.get_user_device_mappings(test_filename)
            
            if persistent_mappings and len(persistent_mappings) == len(test_mappings):
                print("✅ Persistence across restart verified!")
                return True
            else:
                print("❌ Persistence across restart failed!")
                return False
                
        else:
            print("❌ Save operation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def verify_current_mappings():
    """Check what mappings are currently loaded in memory."""
    print("🧠 CHECKING IN-MEMORY MAPPINGS")
    print("=" * 50)
    
    try:
        from services.device_learning_service import get_device_learning_service
        
        learning_service = get_device_learning_service()
        
        print(f"🧠 Loaded mappings in memory: {len(learning_service.learned_mappings)}")
        
        if learning_service.learned_mappings:
            for fingerprint, data in learning_service.learned_mappings.items():
                filename = data.get('filename', 'Unknown')
                device_count = data.get('device_count', 0)
                saved_at = data.get('saved_at', 'Unknown')
                print(f"   - {fingerprint[:8]}: {filename} ({device_count} devices, saved: {saved_at})")
        else:
            print("   (No mappings loaded)")
        
        # Test global store
        try:
            from services.ai_mapping_store import ai_mapping_store
            store_data = ai_mapping_store.all()
            print(f"🌐 Global AI store: {len(store_data)} items")
            if store_data:
                for device, mapping in list(store_data.items())[:3]:
                    source = mapping.get('source', 'unknown')
                    print(f"   - {device}: {source}")
        except ImportError:
            print("⚠️ ai_mapping_store not available")
            
    except Exception as e:
        print(f"❌ Error checking in-memory mappings: {e}")

def main():
    """Run all diagnostic tests."""
    print("🚀 DEVICE MAPPING PERSISTENCE DIAGNOSTICS")
    print("=" * 60)
    print()
    
    # Check storage directory
    check_storage_directory()
    
    # Check current state
    verify_current_mappings()
    print()
    
    # Test save/load cycle
    success = test_save_load_cycle()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 ALL DIAGNOSTICS PASSED - Persistence is working correctly!")
    else:
        print("❌ DIAGNOSTICS FAILED - Persistence is not working!")
    print("=" * 60)

if __name__ == "__main__":
    main()