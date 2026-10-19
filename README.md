# Polarsteps growth scenario model (v0.2)

An outside-in Monte Carlo model of what could bind Polarsteps' growth from 25M to 100M users, built only from public data and Polarsteps' own published user counts. **It is more like a thinking tool for discussion than a forecast.**

**Status:** v0.2. The growth rate is calibrated to published user counts. The market-size inputs are partly sourced (Eurostat) and partly assumed. v0.2 adds an active-user output and a KPI tree. See [What changed in v0.2](#what-changed-in-v02) and [Limitations](#limitations).

## The question

How many years could it take to reach 100M users, how many of those would be active, and which assumptions does the answer depend on most?

## Headline (v0.2, placeholder market multiplier, not a forecast)

100M registered users at about year 5 corresponds to roughly **28M active users** (p10 to p90: 19M to 40M), not 100M. The registered-user count alone makes growth look more dramatic than the active base supports. See [docs/v0.2_results.md](docs/v0.2_results.md).

## What changed in v0.2

| Change | Where |
|---|---|
| **Active users.** Output = cumulative users x `active_share`. A static ratio with no churn, so a rescaling of the same growth curve and not a retention model. Active target: 25M (placeholder, about 100M x the prior mode of `active_share`) | `src/model.py` |
| **KPI tree.** The model targets the acquisition North Star. Retention and monetization are mapped but not modelled. Every metric is a hypothesis | [docs/kpi_tree.md](docs/kpi_tree.md) |
| **v0.1 versus v0.2 comparison.** Cumulative outputs are unchanged (regression check passed) | [docs/v0.2_results.md](docs/v0.2_results.md) |
| **Frozen baseline.** v0.1 results are kept for reference (git tag `v0.1`) | [docs/v0.1_results.md](docs/v0.1_results.md) |

## How it works

The pipeline has three steps, orchestrated by `src/main.py`.

1. **Eurostat import** (`src/eurostat_data_import.py`). Downloads tourism participation (`tin00186`, all trips of 1+ nights, all destinations, % of population aged 15+) and population (`demo_pjanbroad`). Multiplies them into travellers per country and year, and saves CSVs to `data/` and charts to `outputs/`.
2. **Calibration** (`src/calibrate.py`). Draws priors for the model inputs, then solves for `conversion` in each draw so that simulated growth matches the observed user counts (15M in May 2025 and 25M in Aug 2026). The 20M point (Mar 2026) is held out as a check. Saves `data/calibrated_draws.csv`.
3. **Forward model** (`src/model.py`). Simulates monthly growth from 25M (Aug 2026) for each calibrated draw, up to 15 years. Reports the probability of reaching 100M registered users within 3, 5, 8, 10 and 15 years, the same for the active-user target, active users at years 5 and 10, and a sensitivity ranking for each.

### Model structure

Each month, new users come from the loop plus a fading paid effect, scaled by the share of the market still open:

```
k_loop = active_share x invites_per_trip x conversion
k(t) = k_loop x (1 + paid_share_start x (1 - paid_decay)^t)
new users = users x k(t) x (1 - users / addressable_m) / 12
active users = users x active_share
```

Inputs are drawn from triangular (low, mode, high) ranges. `k` is an annual logistic growth rate. It is not a viral K-factor, so the rule of thumb "K above or below 1" does not apply to it.

### Growth structure: loops, not a funnel

The model treats growth as loops. Users who join send invites that bring in more users (the referral loop, `k_loop`), and paid acquisition adds a fading boost on top (`paid_share_start`, `paid_decay`). Both are capped by the share of the addressable market still open. This follows the framing in Reforge's ["Growth Loops are the New Funnels"](https://www.reforge.com/blog/growth-loops): a funnel does not show how one cohort of users leads to the next.

Two things the model does not do. It has no loop cycle time (growth is continuous). And paid acquisition enters as a multiplier on the loop rate, so paid-acquired users are implicitly assumed to invite like everyone else. Whether paid users are as valuable as organic ones is an open question that needs internal data. See [Planned for v0.3](#planned-for-v03).

## Assumptions

| Parameter | Range or source | Status |
|---|---|---|
| `active_share` | 0.15 / 0.25 / 0.40 | Judgement |
| `invites_per_trip` | 2 / 5 / 8 | Judgement. A figure of about 5 invites per trip is reported in the press, but I could not verify it, so treat it as an assumption |
| `conversion` | Solved in calibration | Effective rate, not measured (see Limitations) |
| `addressable_m` | Latest non-2020 EU27 travellers (Eurostat) x adoption share (0.20 / 0.40 / 0.60) x world multiplier (1.0 / 1.5 / 2.5) | Eurostat base is sourced. Adoption share and world multiplier are **placeholders** |
| `paid_share_start` | 0 / 0.15 / 0.35 | Judgement. Needs internal data |
| `paid_decay` | 0.05 / 0.15 / 0.30 | Judgement. Needs internal data |
| Active target | 25M | Placeholder |

Observed Polarsteps user counts used for calibration: 15M (May 2025), 20M (Mar 2026), 25M (Aug 2026), from Polarsteps' own records. Earlier milestones (1M in 2019, 5M in 2022, 10M in 2024) are not used in the fit because the months are unknown.

## Setup and run
```
python -m venv .venv
```

Activate the environment:
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Then install and run:
```
pip install -r requirements.txt
python src/main.py
```

### Command-line options:

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
| `outputs/summary.csv` | Probability of reaching the registered-user target (100M) and the active-user target (25M) within N years, percentiles among runs that reach them, and cumulative and active users at years 5 and 10 |
| `outputs/sensitivity.csv`, `outputs/tornado.png` | Spearman rank correlation of each input with years to 100M registered users |
| `outputs/sensitivity_active.csv` | The same, for years to the active-user target |
| `outputs/years_to_target.png` | Histogram of years to 100M among runs that reach it |
| `outputs/years_to_active_target.png` | Histogram of years to the active-user target among runs that reach it |
| `outputs/eu27_travellers.png` and other Eurostat charts | Produced by the Eurostat import step |

Runs with `--skip-calibration` also write the same files with an `_uncalibrated` suffix.

### Calibrated versus uncalibrated

| Metric | Uncalibrated | Calibrated |
|---|---|---|
| P(reach 100M within 5 years) | 0.0% | 56.7% |
| P(reach 100M within 10 years) | 4.3% | 99.2% |
| P(reach 100M within 15 years) | 21.4% | 99.7% |
| Median time to 100M (runs that reach it) | 12.2 years | 4.9 years |

The raw priors imply a much slower growth rate than Polarsteps' own user history shows. Calibration fixes this by solving for `conversion` so that simulated growth matches the published counts. The uncalibrated run is shown only for contrast.

## Example run (placeholder multiplier, not a forecast)

| Result | Registered users (100M) | Active users (25M) |
|---|---|---|
| Draws kept after calibration | 43,756 of 50,000 | same draws |
| Reach target within 5 years | 56.7% | 64.4% |
| Reach target within 10 years | 99.2% | 92.3% |
| Reach target within 15 years | 99.7% | 93.9% |
| Median years if reached | 4.9 | 4.3 |

| Users (median, p10 to p90 for active) | Today | Year 5 | Year 10 |
|---|---|---|---|
| Registered | 25M | 102M | 158M |
| Active | 6.7M | 27.9M (18.9M to 39.5M) | 43.1M (26.4M to 68.1M) |

**Holdout check (Mar 2026).** The model predicts 20.3M to 22.1M (p10 to p90, median 21.1M). The observed value is 20.0M, which is **below the whole predicted range**. The model overshoots, and I do not treat this as a pass.

**Reading the active-user row.** The active target is reached sooner at first because the median `active_share` (0.27) is above the 0.25 behind the placeholder target. It levels off near 94% because in some draws the active-user ceiling (`addressable_m x active_share`) is below the target, so it can never be reached. The 25M target is a judgement. The year-5 and year-10 levels are the more defensible output.

These figures depend heavily on the placeholder world multiplier, which sets the market ceiling. Do not read them as a prediction.

## Limitations

- **Only the product of the loop inputs is identified.** Growth data pins down only the overall rate k, given the ceiling. Active share, invites, conversion, paid share and paid decay are not separately identified; they are judgement priors, so their individual sensitivity rankings are not meaningful.
- **`active_share` ranks first in the active-user sensitivity partly by definition.** It sets how many registered users the active target needs. This is not evidence that raising active share would speed growth.
- **Implied `conversion` is far above its prior** (median 0.29, against a prior range of 0.02 to 0.12). It absorbs all growth the other inputs do not explain, such as word of mouth and search. It is not a literal invite-to-install rate.
- **Active users are a static ratio.** There is no churn, cohort retention or definition of "active" taken from Polarsteps.
- **Constant growth rate.** Real growth was back-loaded (5M in the last 5 months versus 5M in the 10 months before), and the model overshoots the held-out 20M point (see the holdout check). Deceleration is captured only through market saturation.
- **Market size is the weakest link.** Eurostat covers European residents only. The adoption share and the rest-of-world multiplier are assumptions, and the ceiling drives the long-run results.
- **No seasonality, country split or internal data.** Paid acquisition is a crude fading term, not a spend-response curve.
- **Right-censoring.** Runs that do not reach the target within 15 years have no years-to-target value. Always read the probability of reaching the target first, and the median only second.

## What would improve it

User and active-user counts by country, the paid versus organic acquisition split, referral-attributed installs, and retention by cohort. Each of these would replace one of the judgement inputs above.

## Planned for v0.3

Not part of v0.2. Listed in the order I would do them.

| Item | What it would add | Status |
|---|---|---|
| **Incrementality demo** | A difference-in-differences estimate of a paid campaign on simulated regions with a known true effect, a power calculation for the number of regions and weeks, and a test of what happens when parallel trends fail. This would show how I would measure paid acquisition, which the current model only treats as a fading term. | Planned. Simulated data only, so it shows the method and says nothing about Polarsteps. |
| **Loop cycle-time scenario** | The model has no delay between a user joining and the users they bring in. v0.3 would add a delay of N months as a sensitivity scenario (this will not be a calibrated parameter, since growth data cannot identify it), and check how far the results move. | Planned |
| **Holdout miss** | The model overshoots the 20M holdout. One untested hypothesis is that a delayed loop explains part of the back-loaded growth. A second option is a growth rate that changes over time. | Planned. Hypothesis not tested |
| **Retention layer** | Replace the static `active_share` ratio with a simple retention curve, so that active users can fall as well as rise. | Planned. Needs an assumed curve, since I have no cohort data |
| **Paid versus organic quality** | Allow paid-acquired users to differ from organic ones in how much they invite, instead of assuming they behave the same. | Planned. Needs internal data to calibrate |

Anything calibrated on internal data (retention, the paid versus organic split, referral-attributed installs) would need data that only Polarsteps has. Until then these stay as scenarios: my best guess, from limited knowledge, of how things could unfold. They are not a prediction or forecast.

## Data & other sources

- Eurostat, participation in tourism for personal purposes (`tin00186`)
- Eurostat, population on 1 January by broad age group (`demo_pjanbroad`)
- Polarsteps' published user milestones
- Reforge, ["Growth Loops are the New Funnels"](https://www.reforge.com/blog/growth-loops); Lenny Rachitsky, ["Choosing Your North Star Metric"](https://future.a16z.com/north-star-metrics/); Reforge, ["North Star metrics"](https://www.reforge.com/blog/north-star-metrics) (framing only, see [docs/kpi_tree.md](docs/kpi_tree.md))


Learning log: [appendix.md](appendix.md).