# diagnose_upload_store.py
import sys
sys.path.append('.')

def diagnose_upload_store():
    print(" UPLOAD STORE DIAGNOSTIC")
    print("=" * 50)
    
    # Check the upload store directly
    from utils.upload_store import uploaded_data_store
    
    print(f" Upload store data: {len(uploaded_data_store.get_all_data())} files")
    print(f" Upload store filenames: {uploaded_data_store.get_filenames()}")
    
    # Check storage directory
    import os
    storage_dir = uploaded_data_store.storage_dir
    print(f" Storage directory: {storage_dir}")
    print(f" Directory exists: {os.path.exists(storage_dir)}")
    
    if os.path.exists(storage_dir):
        files = list(storage_dir.glob("*"))
        print(f" Files in storage: {len(files)}")
        for file in files:
            print(f"   {file.name} ({file.stat().st_size} bytes)")
    
    # Check file info
    file_info = uploaded_data_store.get_file_info()
    print(f" File info store: {len(file_info)} entries")
    for name, info in file_info.items():
        print(f"   {name}: {info.get('rows', 0)} rows")

if __name__ == "__main__":
    diagnose_upload_store()