"""Calibrate the priors to Polarsteps' observed user growth.
Only the product k = active_share * invites * conversion * (1 + paid share) is identified by growth data,
so conversion is solved for in each draw; the other priors are kept as drawn.
Usage: python src/calibrate.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

import model

SEED = 42
N_DRAWS = 50_000
OBS = pd.DataFrame({"t": [2025 + 4/12, 2026 + 2/12, 2026 + 7/12], "u": [15.0, 20.0, 25.0]})
FIT_FIRST, FIT_LAST = 0, 2          # rows of OBS used for the fit; the middle row is the holdout check
K_NOISE_SD = 0.10                   # lognormal noise on k (date/rounding uncertainty)
MAX_CONVERSION = 0.5
EU_CSV = Path("data/eurostat_eu27_travellers.csv")
OUT_CSV = Path("data/calibrated_draws.csv")

# addressable_m = EU27 travellers x adoption share x rest-of-world multiplier (triangular, low/mode/high)
ADOPTION_SHARE = (0.20, 0.40, 0.60)    # judgement: share of travellers who would use a trip app
WORLD_MULTIPLIER = (1.0, 1.5, 2.5)     # PLACEHOLDER: non-EU markets relative to EU; replace with sourced values
USE_EUROSTAT_H = True


def eurostat_base_travellers_m(path: Path = EU_CSV) -> float | None:
    if not path.exists():
        return None
    eu = pd.read_csv(path).dropna(subset=["travellers_m"])
    eu = eu[eu["year"] != 2020]
    return float(eu.sort_values("year")["travellers_m"].iloc[-1]) if len(eu) else None


def draw_priors(n: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    d = model.draw_priors(n, seed)
    base = eurostat_base_travellers_m() if USE_EUROSTAT_H else None
    if base is not None:
        d["addressable_m"] = (base * rng.triangular(*ADOPTION_SHARE, n)
                              * rng.triangular(*WORLD_MULTIPLIER, n))
        print(f"addressable_m built from Eurostat base of {base:.0f}M EU travellers")
    else:
        print("Eurostat CSV not found: using placeholder addressable_m prior")
    return d


def implied_k(draws: pd.DataFrame, seed: int = SEED) -> np.ndarray:
    """Logistic growth rate per draw that takes the first fit point to the last."""
    rng = np.random.default_rng(seed + 1)
    t0, u0 = OBS.t.iloc[FIT_FIRST], OBS.u.iloc[FIT_FIRST]
    t1, u1 = OBS.t.iloc[FIT_LAST], OBS.u.iloc[FIT_LAST]
    H = draws["addressable_m"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        k = np.log((u1 / (H - u1)) / (u0 / (H - u0))) / (t1 - t0)
    return k * rng.lognormal(0, K_NOISE_SD, len(draws))


def calibrate(draws: pd.DataFrame) -> pd.DataFrame:
    d = draws.copy()
    d["k"] = implied_k(d)
    d["conversion"] = d["k"] / (d["active_share"] * d["invites_per_trip"] * (1 + d["paid_share_start"]))
    u_last = OBS.u.iloc[FIT_LAST]
    ok = (d["conversion"] > 0) & (d["conversion"] < MAX_CONVERSION) & (d["addressable_m"] > 1.2 * u_last)
    return d[ok].reset_index(drop=True)


def holdout_check(post: pd.DataFrame) -> np.ndarray:
    """Predict the held-out middle observation with the fitted logistic curve."""
    t0, u0 = OBS.t.iloc[FIT_FIRST], OBS.u.iloc[FIT_FIRST]
    t_mid = OBS.t.iloc[1]
    x = (post["addressable_m"] - u0) / u0 * np.exp(-post["k"] * (t_mid - t0))
    return (post["addressable_m"] / (1 + x)).to_numpy()


def main() -> pd.DataFrame:
    draws = draw_priors()
    post = calibrate(draws)
    print(f"Kept {len(post):,} of {len(draws):,} draws")
    cols = list(model.PARAMS) + ["k"]
    print(post[cols].describe(percentiles=[.1, .5, .9]).T[["10%", "50%", "90%"]].round(3))
    pred = holdout_check(post)
    print("Holdout (Mar 2026) predicted users, M, p10/p50/p90:",
          np.percentile(pred, [10, 50, 90]).round(1), "| observed", OBS.u.iloc[1])
    OUT_CSV.parent.mkdir(exist_ok=True)
    post[cols].to_csv(OUT_CSV, index=False)
    return post


if __name__ == "__main__":
    main()