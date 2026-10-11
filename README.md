# Polarsteps growth scenario model (v0.1)

An outside-in Monte Carlo model of what could bind Polarsteps' growth from 25M to 100M users, built only from public data and Polarsteps' own published user counts. It is a thinking tool for discussion, not a forecast.

**Status:** v0.1. The growth rate is calibrated to published user counts. The market-size inputs are partly sourced (Eurostat) and partly assumed. See [Limitations](#limitations).

## The question

How many years could it take to reach 100M users, and which assumptions does the answer depend on most?

## How it works

The pipeline has three steps, orchestrated by `src/main.py`.

1. **Eurostat import** (`src/eurostat_data_import.py`). Downloads tourism participation (`tin00186`, all trips of 1+ nights, all destinations, % of population aged 15+) and population (`demo_pjanbroad`). Multiplies them into travellers per country and year, and saves CSVs to `data/` and charts to `outputs/`.
2. **Calibration** (`src/calibrate.py`). Draws priors for the model inputs, then solves for `conversion` in each draw so that simulated growth matches the observed user counts (15M in May 2025 and 25M in Aug 2026). The 20M point (Mar 2026) is held out as a check. Saves `data/calibrated_draws.csv`.
3. **Forward model** (`src/model.py`). Simulates monthly growth from 25M (Aug 2026) for each calibrated draw, up to 15 years, and reports the probability of reaching 100M within 3, 5, 8, 10 and 15 years plus a sensitivity ranking.

### Model structure

Each month, new users come from the loop plus a fading paid effect, scaled by the share of the market still open:

```
loop rate k_loop = active_share x invites_per_trip x conversion
k(t)             = k_loop x (1 + paid_share_start x (1 - paid_decay)^t)
new users        = users x k(t) x (1 - users / addressable_m) / 12
```

Inputs are drawn from triangular (low, mode, high) ranges.

## Assumptions

| Parameter | Range or source | Status |
|---|---|---|
| `active_share` | 0.15 / 0.25 / 0.40 | Judgement |
| `invites_per_trip` | 2 / 5 / 8 | Judgement (about 5 reported in press; to be verified) |
| `conversion` | Solved in calibration | Effective rate, not measured |
| `addressable_m` | Latest non-2020 EU27 travellers (Eurostat) x adoption share (0.20 / 0.40 / 0.60) x world multiplier (1.0 / 1.5 / 2.5) | Eurostat base is sourced. Adoption share and world multiplier are **placeholders** |
| `paid_share_start` | 0 / 0.15 / 0.35 | Judgement. Needs internal data |
| `paid_decay` | 0.05 / 0.15 / 0.30 | Judgement. Needs internal data |

Observed Polarsteps user counts used for calibration: 15M (May 2025), 20M (Mar 2026), 25M (Aug 2026), from Polarsteps' own records. Earlier milestones (1M in 2019, 5M in 2022, 10M in 2024) are not used in the fit because the months are unknown.

## Setup and run

```
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

Command-line options:

| Command | Eurostat data | Calibration | Model input |
|---|---|---|---|
| `python src/main.py` | Download | Runs | Calibrated draws |
| `python src/main.py --skip-eurostat` | Reuse cached CSVs in `data/` (warns if missing) | Runs | Calibrated draws |
| `python src/main.py --skip-calibration` | Download | Skipped | Raw priors from `PARAMS` |
| `python src/main.py --skip-eurostat --skip-calibration` | Reuse cached CSVs | Skipped | Raw priors from `PARAMS` |

- `--skip-eurostat` only skips the download. If `data/eurostat_eu27_travellers.csv` is missing, calibration still runs, but `addressable_m` falls back to the placeholder range in `PARAMS` and a warning is printed.

- `--skip-calibration` runs the forward model on the raw priors, without fitting them to Polarsteps' observed user counts. It is a comparison run to show why calibration matters, not a result to quote. Its outputs are saved with an `_uncalibrated` suffix (for example `outputs/summary_uncalibrated.csv`), so they never overwrite the calibrated files.

Each module also runs on its own (`python src/calibrate.py`, `python src/model.py`). Requires Python 3.10 or newer.

## Outputs

| File | Content |
|---|---|
| `data/eurostat_eu27_travellers.csv` | EU27 participation, population and travellers by year |
| `data/eurostat_country_travellers.csv` | Same, by country (aggregates excluded) |
| `data/calibrated_draws.csv` | Parameter draws consistent with observed growth |
| `outputs/summary.csv` | Probability of reaching 100M within N years, and percentiles among runs that reach it |
| `outputs/sensitivity.csv`, `outputs/tornado.png` | Spearman rank correlation of each input with years-to-target |
| `outputs/years_to_target.png` | Histogram of years to 100M among runs that reach it |
| `outputs/eu27_travellers.png` and other Eurostat charts | Produced by the Eurostat import step |

Runs with `--skip-calibration` also write `outputs/summary_uncalibrated.csv`, `outputs/sensitivity_uncalibrated.csv`, `outputs/tornado_uncalibrated.png` and `outputs/years_to_target_uncalibrated.png`.

### Calibrated versus uncalibrated

| Result | Calibrated (Eurostat ceiling) | Uncalibrated (raw priors) |
|---|---|---|
| Reach 100M within 5 years | 56.7% | 0.0% |
| Reach 100M within 10 years | 99.2% | 4.3% |
| Reach 100M within 15 years | 99.7% | 21.4% |
| Median years if reached | 4.9 | 12.2 |

The raw priors imply a much slower growth rate than Polarsteps' own user history shows. Calibration fixes this by solving for `conversion` so that simulated growth matches the published counts. The uncalibrated run is shown only for contrast.

## Example run (placeholder multiplier, not a forecast)

| Result | Value |
|---|---|
| Draws kept after calibration | 43,756 of 50,000 |
| Holdout check, Mar 2026 (observed 20.0M) | 20.3 to 22.1M predicted (p10 to p90) |
| Reach 100M within 5 years | 56.7% |
| Reach 100M within 10 years | 99.2% |
| Reach 100M within 15 years | 99.7% |
| Median years if reached | 4.9 |

These figures depend heavily on the placeholder world multiplier, which sets the market ceiling. Do not read them as a prediction.

## Limitations

- **Only the product of the loop inputs is identified.** Growth data fixes the overall rate k. Active share, invites and conversion trade off against each other after calibration, so their individual sensitivity rankings are not meaningful. Only the ceiling (`addressable_m`), paid share, paid decay and k carry real information.
- **Constant growth rate.** Real growth was back-loaded (5M in the last 5 months versus 5M in the 10 months before), and the model overshoots the held-out 20M point slightly. Deceleration is captured only through market saturation.
- **Market size is the weakest link.** Eurostat covers European residents only. The adoption share and the rest-of-world multiplier are assumptions.
- **No churn, seasonality, country split or internal data.** Paid acquisition is a crude fading term, not a spend-response curve.
- **Right-censoring.** Runs that do not reach 100M within 15 years have no years-to-target value. Always read the probability of reaching the target first, and the median only second.

## What would improve it

User and active-user counts by country, the paid versus organic acquisition split, referral-attributed installs, and retention by cohort. Each of these would replace one of the judgement inputs above.

## Data sources

- Eurostat, participation in tourism for personal purposes (`tin00186`)
- Eurostat, population on 1 January by broad age group (`demo_pjanbroad`)
- Polarsteps' published user milestones
