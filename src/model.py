"""Forward Monte Carlo: years for Polarsteps to reach the target user count.
Works on any DataFrame of parameter draws (priors or calibrated posterior).
Usage: python src/model.py   (uses data/calibrated_draws.csv if present, else priors)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 42
N_DRAWS = 20_000
START_USERS_M = 25.0      # Aug 2026, Polarsteps' own records
TARGET_USERS_M = 100.0
HORIZON_YEARS = 15
HORIZONS = (3, 5, 8, 10)  # report P(reach target within N years)

OUT_DIR = Path("outputs")
DATA_DIR = Path("data")
CALIBRATED_CSV = DATA_DIR / "calibrated_draws.csv"

# (low, mode, high) triangular priors. active_share/invites/paid_* are judgement, not sourced.
# addressable_m is overridden by calibrate.py when Eurostat data is available.
PARAMS = {
    "active_share":     (0.15, 0.25, 0.40),
    "invites_per_trip": (2.0, 5.0, 8.0),
    "conversion":       (0.02, 0.05, 0.12),
    "addressable_m":    (150.0, 250.0, 400.0),
    "paid_share_start": (0.0, 0.15, 0.35),
    "paid_decay":       (0.05, 0.15, 0.30),
}


def draw_priors(n: int = N_DRAWS, seed: int = SEED, params: dict = PARAMS) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({k: rng.triangular(*v, size=n) for k, v in params.items()})


def simulate(draws: pd.DataFrame, start=START_USERS_M, target=TARGET_USERS_M,
             years=HORIZON_YEARS) -> np.ndarray:
    """Monthly logistic loop plus fading paid effect. Returns years-to-target (NaN = not reached)."""
    loop_k = (draws["active_share"] * draws["invites_per_trip"] * draws["conversion"]).to_numpy()
    ps = draws["paid_share_start"].to_numpy()
    decay = draws["paid_decay"].to_numpy()
    cap = draws["addressable_m"].to_numpy()
    users = np.full(len(draws), start)
    hit = np.full(len(draws), np.nan)
    for m in range(1, years * 12 + 1):
        t = m / 12
        k_t = loop_k * (1 + ps * (1 - decay) ** t)
        users = users + users * k_t * np.clip(1 - users / cap, 0, 1) / 12
        hit = np.where(np.isnan(hit) & (users >= target), t, hit)
    return hit


def summarise(years_to_target: np.ndarray) -> pd.Series:
    reached = ~np.isnan(years_to_target)
    out = {f"p_reach_within_{h}y": np.mean(reached & (years_to_target <= h)) for h in HORIZONS}
    out[f"p_reach_within_{HORIZON_YEARS}y"] = reached.mean()
    if reached.any():
        out.update({"p10_years_if_reached": np.nanpercentile(years_to_target, 10),
                    "median_years_if_reached": np.nanmedian(years_to_target),
                    "p90_years_if_reached": np.nanpercentile(years_to_target, 90)})
    return pd.Series(out)


def sensitivity(draws: pd.DataFrame, years_to_target: np.ndarray) -> pd.Series:
    """Spearman rank correlation with years-to-target; unreached runs ranked last."""
    y = pd.Series(np.where(np.isnan(years_to_target), HORIZON_YEARS + 1, years_to_target))
    cols = [c for c in PARAMS if c in draws.columns and draws[c].nunique() > 1]
    return pd.Series({c: draws[c].reset_index(drop=True).corr(y, method="spearman") for c in cols}) \
        .sort_values(key=abs)


def plot(years_to_target: np.ndarray, sens: pd.Series, label: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    reached = ~np.isnan(years_to_target)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(years_to_target[reached], bins=np.arange(0, HORIZON_YEARS + 1, 0.5), color="#2a7fff")
    ax.set(xlabel=f"Years to {TARGET_USERS_M:.0f}M users",
           ylabel="Simulations",
           title=f"{label}: {reached.mean():.0%} reach target within {HORIZON_YEARS}y")
    fig.tight_layout(); fig.savefig(OUT_DIR / "years_to_target.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(sens.index, sens.values, color="#ff7a2a")
    ax.set(xlabel="Spearman correlation with years-to-target", title="What moves the answer most")
    fig.tight_layout(); fig.savefig(OUT_DIR / "tornado.png", dpi=150); plt.close(fig)


def run(draws: pd.DataFrame, label: str) -> pd.Series:
    OUT_DIR.mkdir(exist_ok=True)
    years = simulate(draws)
    summary = summarise(years)
    sens = sensitivity(draws, years)
    summary.to_csv(OUT_DIR / "summary.csv", header=["value"])
    sens.to_csv(OUT_DIR / "sensitivity.csv", header=["spearman"])
    plot(years, sens, label)
    return summary


def main() -> None:
    if CALIBRATED_CSV.exists():
        draws, label = pd.read_csv(CALIBRATED_CSV), "Calibrated"
    else:
        draws, label = draw_priors(), "Uncalibrated priors"
    print(f"Running model on {len(draws):,} draws ({label})")
    summary = run(draws, label)
    print(summary.round(3).to_string())


if __name__ == "__main__":
    main()