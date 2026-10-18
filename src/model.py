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
ACTIVE_TARGET_M = 25.0    # PLACEHOLDER: ~100M x prior mode of active_share (0.25); a judgement, not a Polarsteps figure

OUT_DIR = Path("outputs")
DATA_DIR = Path("data")
CALIBRATED_CSV = DATA_DIR / "calibrated_draws.csv"

# (low, mode, high) triangular priors. active_share/invites/paid_ values are judgement, not sourced.
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


# def simulate(draws: pd.DataFrame, start=START_USERS_M, target=TARGET_USERS_M,
#              years=HORIZON_YEARS) -> np.ndarray:
#     """Monthly logistic loop plus fading paid effect. Returns years-to-target (NaN = not reached)."""
#     loop_k = (draws["active_share"] * draws["invites_per_trip"] * draws["conversion"]).to_numpy()
#     ps = draws["paid_share_start"].to_numpy()
#     decay = draws["paid_decay"].to_numpy()
#     cap = draws["addressable_m"].to_numpy()
#     users = np.full(len(draws), start)
#     hit = np.full(len(draws), np.nan)
#     for m in range(1, years * 12 + 1):
#         t = m / 12
#         k_t = loop_k * (1 + ps * (1 - decay) ** t)
#         users = users + users * k_t * np.clip(1 - users / cap, 0, 1) / 12
#         hit = np.where(np.isnan(hit) & (users >= target), t, hit)
#     return hit


def simulate(draws: pd.DataFrame, start=START_USERS_M, target=TARGET_USERS_M,
             years=HORIZON_YEARS, active_target=ACTIVE_TARGET_M):
    """Monthly logistic loop plus fading paid effect.
    Returns (years to cumulative target, years to active-user target, cumulative users at HORIZONS).
    NaN = not reached. Active users = cumulative users x active_share (static ratio, no churn)."""
    loop_k = (draws["active_share"] * draws["invites_per_trip"] * draws["conversion"]).to_numpy()
    ps = draws["paid_share_start"].to_numpy()
    decay = draws["paid_decay"].to_numpy()
    cap = draws["addressable_m"].to_numpy()
    share = draws["active_share"].to_numpy()
    users = np.full(len(draws), start)
    hit = np.full(len(draws), np.nan)
    hit_active = np.full(len(draws), np.nan)
    snapshots = {}
    for m in range(1, years * 12 + 1):
        t = m / 12
        k_t = loop_k * (1 + ps * (1 - decay) ** t)
        users = users + users * k_t * np.clip(1 - users / cap, 0, 1) / 12
        hit = np.where(np.isnan(hit) & (users >= target), t, hit)
        hit_active = np.where(np.isnan(hit_active) & (users * share >= active_target), t, hit_active)
        if m % 12 == 0 and m // 12 in HORIZONS:
            snapshots[m // 12] = users.copy()
    return hit, hit_active, snapshots


# def summarise(years_to_target: np.ndarray) -> pd.Series:
#     reached = ~np.isnan(years_to_target)
#     out = {f"p_reach_within_{h}y": np.mean(reached & (years_to_target <= h)) for h in HORIZONS}
#     out[f"p_reach_within_{HORIZON_YEARS}y"] = reached.mean()
#     if reached.any():
#         out.update({"p10_years_if_reached": np.nanpercentile(years_to_target, 10),
#                     "median_years_if_reached": np.nanmedian(years_to_target),
#                     "p90_years_if_reached": np.nanpercentile(years_to_target, 90)})
#     return pd.Series(out)


def summarise(years_to_target: np.ndarray, years_to_active: np.ndarray = None,
              snapshots: dict = None, active_share: np.ndarray = None) -> pd.Series:
    reached = ~np.isnan(years_to_target)
    out = {f"p_reach_within_{h}y": np.mean(reached & (years_to_target <= h)) for h in HORIZONS}
    out[f"p_reach_within_{HORIZON_YEARS}y"] = reached.mean()
    if reached.any():
        out.update({"p10_years_if_reached": np.nanpercentile(years_to_target, 10),
                    "median_years_if_reached": np.nanmedian(years_to_target),
                    "p90_years_if_reached": np.nanpercentile(years_to_target, 90)})
    if years_to_active is not None:
        reached_a = ~np.isnan(years_to_active)
        out.update({f"p_active_reach_within_{h}y": np.mean(reached_a & (years_to_active <= h))
                    for h in HORIZONS})
        out[f"p_active_reach_within_{HORIZON_YEARS}y"] = reached_a.mean()
        if reached_a.any():
            out.update({"active_p10_years_if_reached": np.nanpercentile(years_to_active, 10),
                        "active_median_years_if_reached": np.nanmedian(years_to_active),
                        "active_p90_years_if_reached": np.nanpercentile(years_to_active, 90)})
    if snapshots is not None and active_share is not None:
        out["active_users_m_p50_today"] = float(np.median(START_USERS_M * active_share))
        for h in (5, 10):
            if h in snapshots:
                a = snapshots[h] * active_share
                out.update({f"cumulative_users_m_p50_{h}y": float(np.median(snapshots[h])),
                            f"active_users_m_p10_{h}y": float(np.percentile(a, 10)),
                            f"active_users_m_p50_{h}y": float(np.percentile(a, 50)),
                            f"active_users_m_p90_{h}y": float(np.percentile(a, 90))})
    return pd.Series(out)


def sensitivity(draws: pd.DataFrame, years_to_target: np.ndarray) -> pd.Series:
    """Spearman rank correlation with years-to-target; unreached runs ranked last."""
    y = pd.Series(np.where(np.isnan(years_to_target), HORIZON_YEARS + 1, years_to_target))
    cols = [c for c in PARAMS if c in draws.columns and draws[c].nunique() > 1]
    return pd.Series({c: draws[c].reset_index(drop=True).corr(y, method="spearman") for c in cols}) \
        .sort_values(key=abs)


def plot(years_to_target: np.ndarray, sens: pd.Series, label: str, suffix: str = "") -> None:
    OUT_DIR.mkdir(exist_ok=True)
    reached = ~np.isnan(years_to_target)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(years_to_target[reached], bins=np.arange(0, HORIZON_YEARS + 1, 0.5), color="#2a7fff")
    ax.set(xlabel=f"Years to {TARGET_USERS_M:.0f}M users",
           ylabel="Simulations",
           title=f"{label}: {reached.mean():.0%} reach target within {HORIZON_YEARS}y")
    fig.tight_layout(); fig.savefig(OUT_DIR / f"years_to_target{suffix}.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(sens.index, sens.values, color="#ff7a2a")
    ax.set(xlabel="Spearman correlation with years-to-target", title="What moves the answer most")
    fig.tight_layout(); fig.savefig(OUT_DIR / f"tornado{suffix}.png", dpi=150); plt.close(fig)


def plot_active(years_to_active: np.ndarray, label: str, suffix: str = "") -> None:
    OUT_DIR.mkdir(exist_ok=True)
    reached = ~np.isnan(years_to_active)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(years_to_active[reached], bins=np.arange(0, HORIZON_YEARS + 1, 0.5), color="#2aa876")
    ax.set(xlabel=f"Years to {ACTIVE_TARGET_M:.0f}M active users",
           ylabel="Simulations",
           title=f"{label}: {reached.mean():.0%} reach active target within {HORIZON_YEARS}y")
    fig.tight_layout(); fig.savefig(OUT_DIR / f"years_to_active_target{suffix}.png", dpi=150); plt.close(fig)


def run(draws: pd.DataFrame, label: str, suffix: str = "") -> pd.Series:
    OUT_DIR.mkdir(exist_ok=True)
    years, years_active, snapshots = simulate(draws)
    summary = summarise(years, years_active, snapshots, draws["active_share"].to_numpy())
    sens = sensitivity(draws, years)
    sens_active = sensitivity(draws, years_active)
    summary.to_csv(OUT_DIR / f"summary{suffix}.csv", header=["value"])
    sens.to_csv(OUT_DIR / f"sensitivity{suffix}.csv", header=["spearman"])
    sens_active.to_csv(OUT_DIR / f"sensitivity_active{suffix}.csv", header=["spearman"])
    plot(years, sens, label, suffix)
    plot_active(years_active, label, suffix)
    return summary


def main(use_calibrated: bool = True) -> None:
    suffix = ""
    if use_calibrated and CALIBRATED_CSV.exists():
        draws, label = pd.read_csv(CALIBRATED_CSV), "Calibrated"
    else:
        if use_calibrated:
            print(f"WARNING: {CALIBRATED_CSV} not found, falling back to raw priors")
        draws, label, suffix = draw_priors(), "Uncalibrated priors", "_uncalibrated"
    print(f"Running model on {len(draws):,} draws ({label})")
    summary = run(draws, label, suffix)
    print(summary.round(3).to_string())


if __name__ == "__main__":
    main()