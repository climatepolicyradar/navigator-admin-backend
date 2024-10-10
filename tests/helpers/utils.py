import glob
import os
from typing import Optional, Union


def remove_trigger_cols_from_result(
    data: Union[dict, list]
) -> Optional[Union[dict, list]]:
    """Remove created and last modified columns from test response data."""

    if isinstance(data, list):
        assert all(
            field in col for col in data for field in ("created", "last_modified")
        )
        data = sorted(data, key=lambda d: d["import_id"])
        return [
            {
                k: v if not isinstance(v, list) else sorted(v)
                for k, v in col.items()
                if k not in ("created", "last_modified")
            }
            for col in data
        ]
    if isinstance(data, dict):
        assert all(field in data for field in ("created", "last_modified"))
        return {k: v for k, v in data.items() if k not in ("created", "last_modified")}

    return None


def cleanup_local_files(file: str):
    """Remove all files in the specified directory."""
    files = glob.glob(file)
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error deleting file {f}: {e}")
