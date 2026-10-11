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
    parser.add_argument("--skip-calibration", action="store_true",
                        help="skip calibration and run the model on the raw PARAMS priors")
    args = parser.parse_args()

    print("== 1/3 Eurostat import ==")
    if args.skip_eurostat:
        print("Skipped (using cached CSVs)")
    else:
        eurostat_data_import.main()

    # with or without eurostat data, calibrate.py will calibrate the growth rate (k) to the observed user counts (Polarsteps' own data) and calculates the implied conversion rate for each draw. If eurostat data is available, it will also calibrate the addressable market size (addressable_m) to the Eurostat travellers data.
    print("\n== 2/3 Calibration ==")
    if args.skip_calibration:
        print("Skipped (model will use raw PARAMS priors; results are NOT calibrated)")
    else:
        calibrate.main()

    print("\n== 3/3 Forward model ==")
    model.main(use_calibrated=not args.skip_calibration)


if __name__ == "__main__":
    main()