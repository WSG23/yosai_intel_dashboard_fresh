"""Script to migrate a pickle file to Parquet format using :class:`StorageManager`."""
from __future__ import annotations

from pathlib import Path

from .storage_manager import StorageManager


def main() -> None:
    """Migrate ``Demo3_data_copy.csv.pkl`` to Parquet and load it back."""
    storage = StorageManager()
    pkl_file = Path("Demo3_data_copy.csv.pkl")
    success, message = storage.migrate_pkl_to_parquet(pkl_file)
    print(message)
    if success:
        df, err = storage.load_dataframe(pkl_file.with_suffix("").name)
        if err:
            print(f"Load error: {err}")
        else:
            print(df.head())


if __name__ == "__main__":
    main()
