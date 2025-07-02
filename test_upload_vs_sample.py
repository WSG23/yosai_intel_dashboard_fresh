# test_upload_vs_sample.py
def check_data_source():
    from pages.file_upload import get_uploaded_data
    uploaded = get_uploaded_data()
    
    print(f" Uploaded files: {len(uploaded) if uploaded else 0}")
    
    if uploaded:
        for filename, df in uploaded.items():
            print(f"   {filename}: {len(df)} rows")
            
            # Check if it looks like sample data
            if len(df) in [100, 132, 150, 1000, 10000]:
                print(f"    SUSPICIOUS: Matches sample data row count!")
                
            # Check column patterns
            if 'person_id' in df.columns and df['person_id'].astype(str).str.contains('EMP').any():
                print(f"    CONTAINS SAMPLE DATA PATTERNS!")
    else:
        print("   No uploaded data found")

check_data_source()