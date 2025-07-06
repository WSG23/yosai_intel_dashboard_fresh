#!/usr/bin/env python3
"""
Investigate what data is actually loaded in the system
"""
import json
import os
from pathlib import Path

import pandas as pd


def investigate_data():
    """Check what data the system actually has"""

    print("🔍 INVESTIGATING DATA SITUATION")
    print("=" * 50)

    # Check upload directory
    upload_dir = Path("temp/uploaded_data")
    print(f"\n📁 Upload Directory: {upload_dir}")

    if upload_dir.exists():
        files = list(upload_dir.glob("*"))
        print(f"Files found: {len(files)}")
        for f in files:
            size = f.stat().st_size if f.is_file() else 0
            print(f"  {f.name}: {size:,} bytes ({size/1024:.1f} KB)")
    else:
        print("❌ Upload directory doesn't exist")

    # Check file_info.json
    info_file = upload_dir / "file_info.json"
    if info_file.exists():
        print(f"\n📋 file_info.json contents:")
        with open(info_file, "r") as f:
            info = json.load(f)
        for filename, details in info.items():
            print(f"  {filename}:")
            print(f"    Rows: {details.get('rows', 'unknown'):,}")
            print(f"    Columns: {details.get('columns', 'unknown')}")
            print(f"    Size: {details.get('size_mb', 'unknown')} MB")

    # Try to load the parquet file directly
    parquet_file = upload_dir / "Demo3_data_copy.csv.parquet"
    if parquet_file.exists():
        print(f"\n📊 Loading parquet file directly...")
        try:
            df = pd.read_parquet(parquet_file)
            print(f"  Actual rows in parquet: {len(df):,}")
            print(f"  Actual columns: {len(df.columns)}")
            print(f"  Column names: {list(df.columns)}")
            print(f"  Memory usage: {df.memory_usage(deep=True).sum()/1024:.1f} KB")

            # Show first few rows
            print(f"\n📋 First 3 rows:")
            print(df.head(3).to_string())

        except Exception as e:
            print(f"  ❌ Error loading parquet: {e}")

    # Search for large .pkl files in project
    print(f"\n🔍 Searching for .pkl files in project...")
    project_root = Path(".")
    pkl_files = list(project_root.rglob("*.pkl"))

    if pkl_files:
        print(f"Found {len(pkl_files)} .pkl files:")
        for pkl in pkl_files:
            if pkl.is_file():
                size = pkl.stat().st_size
                print(f"  {pkl}: {size:,} bytes ({size/1024/1024:.1f} MB)")
    else:
        print("  No .pkl files found in project")

    # Search for any large files
    print(f"\n🔍 Searching for files > 5MB...")
    large_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            filepath = Path(root) / file
            try:
                if filepath.stat().st_size > 5 * 1024 * 1024:  # 5MB
                    large_files.append(filepath)
            except OSError:
                pass

    if large_files:
        print(f"Found {len(large_files)} large files:")
        for f in large_files[:10]:  # Show first 10
            size = f.stat().st_size
            print(f"  {f}: {size:,} bytes ({size/1024/1024:.1f} MB)")
    else:
        print("  No large files found")

    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("1. Check the .pkl file locations above")
    print("2. The parquet file contains the actual loaded data")
    print("3. If you find your 17MB .pkl file, we can convert it")


if __name__ == "__main__":
    investigate_data()
