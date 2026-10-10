"""Calibrate the composite growth rate to Polarsteps's reported user milestones."""

import numpy as np, pandas as pd

# Month/day for 2019, 2022, 2024 are ASSUMED mid-year: the source gives only the year.
OBS = pd.DataFrame({
    "date": pd.to_datetime(["2019-07-01", "2022-07-01", "2024-07-01",
                            "2025-05-15", "2026-03-15", "2026-08-15"]),
    "users_m": [1, 5, 10, 15, 20, 25]})
OBS["t"] = (OBS["date"] - OBS["date"].iloc[0]).dt.days / 365.25


def logistic(t, u0, r, H):
    return H / (1 + (H / u0 - 1) * np.exp(-r * t))


def fit_rate(obs, H, grid=np.linspace(0.05, 1.5, 1451)):
    """Best-fit continuous growth rate r for a logistic anchored at the first row of obs."""
    t = obs["t"].values - obs["t"].values[0]
    u = obs["users_m"].values
    sse = [np.sum((np.log(logistic(t, u[0], r, H)) - np.log(u)) ** 2) for r in grid]
    return grid[int(np.argmin(sse))], min(sse)


def calibrate(H_values=(150, 250, 400)):
    rows = []
    windows = {"all_history": OBS, "since_2024": OBS.iloc[2:], "last_12m": OBS.iloc[3:]}
    for name, w in windows.items():
        for H in H_values:
            r, sse = fit_rate(w, H)
            rows.append((name, H, round(r, 3), round(np.exp(r) - 1, 3), round(sse, 4)))
    return pd.DataFrame(rows, columns=["window", "addressable_m", "r_cont", "annual_growth", "sse"])


def years_to_target(u0, r, H, target=100.0):
    return np.log((target / (H - target)) / (u0 / (H - u0))) / r


if __name__ == "__main__":
    res = calibrate(); print(res.to_string(index=False))
    for _, row in res.iterrows():
        print(row.window, row.addressable_m, round(years_to_target(25, row.r_cont, row.addressable_m), 1))
    res.to_csv("outputs/calibration.csv", index=False)