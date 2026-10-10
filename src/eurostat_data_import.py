"""Eurostat travellers pipeline: fetch -> build -> save CSVs -> plot.
Usage: python src/eurostat_pipeline.py
"""
from pathlib import Path

import eurostat
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("data")
OUT_DIR = Path("outputs")
GEO = "geo\\TIME_PERIOD"
YEAR_MIN, YEAR_MAX = 2014, 2025
DURATION = "N_GE1" # 1+ night trips = all trips
SELECTED = ["NL", "FR", "DE", "ES", "IT"]


def year_cols(df: pd.DataFrame) -> list:
    return [c for c in df.columns if str(c).isdigit() and YEAR_MIN <= int(c) <= YEAR_MAX]


def fetch() -> tuple[pd.DataFrame, pd.DataFrame]:
    part = eurostat.get_data_df("tin00186")        # participation, % of population 15+
    pop = eurostat.get_data_df("demo_pjanbroad")   # population on 1 Jan
    assert DURATION in part["duration"].unique(), f"{DURATION} missing: {part['duration'].unique()}"
    return part, pop


def build_participation(part: pd.DataFrame) -> pd.DataFrame:
    p = part[(part["duration"] == DURATION) & (part["c_dest"] == "WORLD") & (part["unit"] == "PC_POP")]
    long = p.melt(id_vars=[GEO], value_vars=year_cols(p), var_name="year", value_name="part_pct")
    long["year"] = long["year"].astype(int)
    return long


def build_population(pop: pd.DataFrame) -> pd.DataFrame:
    p = pop[pop["age"].isin(["Y15-64", "Y_GE65"]) & (pop["sex"] == "T") & (pop["unit"] == "NR")]
    long = p.melt(id_vars=[GEO], value_vars=year_cols(p), var_name="year", value_name="pop")
    long = long.groupby([GEO, "year"], as_index=False)["pop"].sum(min_count=2)
    long["year"] = long["year"].astype(int)
    return long


def build_travellers(part: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    df = build_participation(part).merge(build_population(pop), on=[GEO, "year"], how="inner")
    df = df.rename(columns={GEO: "geo"})
    df["travellers_m"] = df["pop"] * df["part_pct"] / 100 / 1e6
    return df.dropna(subset=["travellers_m"]).sort_values(["geo", "year"]).reset_index(drop=True)


def split_outputs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    eu = df[df["geo"] == "EU27_2020"].copy()
    eu["pop_m"] = eu["pop"] / 1e6
    eu = eu[["year", "part_pct", "pop_m", "travellers_m"]].round(3)
    countries = df[~df["geo"].str.startswith(("EU", "EA"))].round(3)
    return eu, countries


def check(eu: pd.DataFrame) -> None:
    row = eu[eu["year"] == 2023]
    if len(row):
        print(f"2023 EU27 participation: {row['part_pct'].iloc[0]:.1f}% (expect about 65)")


def save(eu: pd.DataFrame, countries: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    eu.to_csv(DATA_DIR / "eurostat_eu27_travellers.csv", index=False)
    countries.to_csv(DATA_DIR / "eurostat_country_travellers.csv", index=False)


def _save_fig(fig, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, dpi=150)
    plt.close(fig)


def plot_all(eu: pd.DataFrame, ctry: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(eu["year"], eu["travellers_m"], marker="o", color="#2a7fff")
    ax.axvspan(2019.5, 2021.5, color="grey", alpha=0.15, label="COVID years")
    ax.set(title="EU27 travellers (1+ night trips, 15+)", xlabel="Year", ylabel="Travellers (M)")
    ax.legend()
    _save_fig(fig, "eu27_travellers.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(eu["year"], eu["part_pct"], marker="o", color="#ff7a2a")
    ax.set(title="EU27 participation (% of population 15+)", xlabel="Year", ylabel="%")
    _save_fig(fig, "eu27_participation.png")

    latest = ctry.sort_values("year").groupby("geo").tail(1)
    top = latest.nlargest(15, "travellers_m").iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(top["geo"] + " (" + top["year"].astype(str) + ")", top["travellers_m"], color="#2a7fff")
    ax.set(title="Top 15 countries by travellers (latest year)", xlabel="Travellers (M)")
    _save_fig(fig, "top_countries_travellers.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for g, d in ctry[ctry["geo"].isin(SELECTED)].groupby("geo"):
        ax.plot(d["year"], d["part_pct"], marker="o", label=g)
    ax.set(title="Participation, selected countries (%)", xlabel="Year", ylabel="%")
    ax.legend()
    _save_fig(fig, "participation_selected.png")


def main() -> None:
    part, pop = fetch()
    df = build_travellers(part, pop)
    eu, countries = split_outputs(df)
    print(eu.to_string(index=False))
    check(eu)
    print("Countries:", countries["geo"].nunique())
    save(eu, countries)
    plot_all(eu, countries)
    print("Saved CSVs to", DATA_DIR, "and charts to", OUT_DIR)


if __name__ == "__main__":
    main()