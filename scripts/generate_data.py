"""Regenerate the deterministic synthetic raw and cleaned order datasets."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import save_sample_data


if __name__ == "__main__":
    raw_path, clean_path = save_sample_data()
    print(f"Raw sample:   {raw_path}")
    print(f"Clean sample: {clean_path}")
