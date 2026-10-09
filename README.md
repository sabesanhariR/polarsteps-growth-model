# Polarsteps growth scenario model (v0.1)

Outside-in model of what could bind growth between 20M and 100M users, using public data only.

**Status:** v0.1, a skeleton. Parameter ranges are placeholders until sourced.

## Question
How many years to 100M users, and which assumption moves the answer most?

## Approach
1. Loop: active travellers x people reached x conversion = new users per year.
2. Saturation: growth slows as users approach the addressable market.
3. Paid add-on: paid-driven users with diminishing returns.
4. Monte Carlo over triangular ranges; Spearman sensitivity.

## Assumptions and sources
| Parameter | Range (low/mode/high) | Source | Confidence |
|---|---|---|---|
| active_share | 0.15 / 0.25 / 0.40 | TODO | Low |
| invites_per_trip | 2 / 5 / 8 | TODO (reported ~5) | Low |
| conversion | 0.02 / 0.05 / 0.12 | TODO | Very low |
| addressable_m | 150 / 250 / 400 | TODO (Eurostat, UN Tourism) | Low |
| paid_share_start | 0 / 0.15 / 0.35 | TODO | Very low |
| paid_decay | 0.05 / 0.15 / 0.30 | TODO | Very low |

## Limitations
Annual steps, no churn, no seasonality, no country split, and no internal data. Results show relative sensitivity, not forecasts.

## Run
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/model.py
```
