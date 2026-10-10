"""Run the whole chain: Eurostat import -> calibration -> forward model.
Usage (from anywhere): python src/main.py [--skip-eurostat]
"""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # all modules use paths relative to the project root

import calibrate
import eurostat_data_import
import model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-eurostat", action="store_true",
                        help="reuse existing CSVs in data/ instead of downloading")
    args = parser.parse_args()

    print("== 1/3 Eurostat import ==")
    if args.skip_eurostat:
        print("Skipped (using cached CSVs)")
    else:
        eurostat_data_import.main()

    print("\n== 2/3 Calibration ==")
    calibrate.main()

    print("\n== 3/3 Forward model ==")
    model.main()


if __name__ == "__main__":
    main()