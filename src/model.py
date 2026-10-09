"""Polarsteps growth scenario model v0.1 (outside-in, public data only).
All parameter ranges are PLACEHOLDERS: replace them with sourced values and cite them in the README.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
N = 20_000
START_USERS_M = 20.0
TARGET_USERS_M = 100.0
MAX_YEARS = 15

# (low, mode, high) triangular ranges -- PLACEHOLDERS, to be sourced
PARAMS = {
    "active_share":      (0.15, 0.25, 0.40),  # share of users who take a tracked trip in a year
    "invites_per_trip":  (2.0, 5.0, 8.0),     # people reached per active traveller (reported ~5)
    "conversion":        (0.02, 0.05, 0.12),  # share of reached people who become new users
    "addressable_m":     (150, 250, 400),     # headroom: users the market can support (M)
    "paid_share_start":  (0.0, 0.15, 0.35),   # paid-driven new users as share of loop new users, year 0
    "paid_decay":        (0.05, 0.15, 0.30),  # diminishing returns on paid per year
}


def draw(n, rng):
    return {k: rng.triangular(*v, size=n) for k, v in PARAMS.items()}


def simulate(p, start=START_USERS_M, target=TARGET_USERS_M, max_years=MAX_YEARS):
    """Annual loop with saturation. Returns years-to-target (NaN if not reached)."""
    n = len(p["active_share"])
    users = np.full(n, start)
    years = np.full(n, np.nan)
    paths = np.zeros((max_years + 1, n))
    paths[0] = users
    for t in range(1, max_years + 1):
        loop_new = users * p["active_share"] * p["invites_per_trip"] * p["conversion"]
        paid_new = loop_new * p["paid_share_start"] * (1 - p["paid_decay"]) ** (t - 1)
        saturation = np.clip(1 - users / p["addressable_m"], 0, 1)
        users = users + (loop_new + paid_new) * saturation
        paths[t] = users
        hit = np.isnan(years) & (users >= target)
        years[hit] = t
    return years, paths


def sensitivity(p, years):
    """Spearman rank correlation of each input with years-to-target (unreached = MAX_YEARS+1)."""
    y = pd.Series(np.where(np.isnan(years), MAX_YEARS + 1, years))
    return pd.Series({k: pd.Series(v).corr(y, method="spearman") for k, v in p.items()}) \
        .sort_values(key=abs)


def run(outdir="outputs"):
    rng = np.random.default_rng(SEED)
    p = draw(N, rng)
    years, paths = simulate(p)
    reached = ~np.isnan(years)
    summary = {
        "share_reaching_target": reached.mean(),
        "p10_years": np.nanpercentile(years, 10),
        "median_years": np.nanmedian(years),
        "p90_years": np.nanpercentile(years, 90),
    }
    pd.Series(summary).to_csv(f"{outdir}/summary.csv")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(years[reached], bins=np.arange(0.5, MAX_YEARS + 1.5), color="#2a7fff")
    ax.set(xlabel=f"Years to {TARGET_USERS_M:.0f}M users", ylabel="Simulations",
           title=f"Years to {TARGET_USERS_M:.0f}M ({reached.mean():.0%} reach it within {MAX_YEARS}y)")
    fig.tight_layout(); fig.savefig(f"{outdir}/years_to_target.png", dpi=150); plt.close(fig)

    s = sensitivity(p, years)
    s.to_csv(f"{outdir}/sensitivity.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(s.index, s.values, color="#ff7a2a")
    ax.set(xlabel="Rank correlation with years-to-target", title="What moves the answer most")
    fig.tight_layout(); fig.savefig(f"{outdir}/tornado.png", dpi=150); plt.close(fig)
    return summary, s


if __name__ == "__main__":
    summary, s = run()
    print(summary); print(s)