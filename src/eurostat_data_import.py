# pip install eurostat pandas
import os
import pandas as pd
import eurostat
import matplotlib.pyplot as plt

OUT_DIR = "data"
PLOT_OUT = "outputs"
GEO = "geo\\TIME_PERIOD"
YEAR_MIN, YEAR_MAX = 2014, 2025
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLOT_OUT, exist_ok=True)

part = eurostat.get_data_df("tin00186")       # participation, % of population aged 15+
pop = eurostat.get_data_df("demo_pjanbroad")  # population on 1 Jan, broad age groups

print("duration labels:", part["duration"].unique())
print("c_dest labels:", part["c_dest"].unique())
print("unit labels:", part["unit"].unique())
print("age labels:", pop["age"].unique())

# 1) participation: all trips (1+ nights), all destinations, % of population
assert "N_GE1" in part["duration"].unique(), "N_GE1 not found - check duration labels above"
part_t = part[(part["duration"] == "N_GE1") & (part["c_dest"] == "WORLD") & (part["unit"] == "PC_POP")]
p_years = [c for c in part_t.columns if str(c).isdigit() and YEAR_MIN <= int(c) <= YEAR_MAX]
part_long = part_t.melt(id_vars=[GEO], value_vars=p_years, var_name="year", value_name="part_pct")
part_long["year"] = part_long["year"].astype(int)

# 2) population aged 15+ (sum of 15-64 and 65+), both sexes
pop15 = pop[pop["age"].isin(["Y15-64", "Y_GE65"]) & (pop["sex"] == "T") & (pop["unit"] == "NR")]
pop_years = [c for c in pop15.columns if str(c).isdigit() and YEAR_MIN <= int(c) <= YEAR_MAX]
pop_long = (pop15.melt(id_vars=[GEO], value_vars=pop_years, var_name="year", value_name="pop")
                 .groupby([GEO, "year"], as_index=False)["pop"].sum(min_count=2))
pop_long["year"] = pop_long["year"].astype(int)

# 3) merge and compute travellers (millions)
df = part_long.merge(pop_long, on=[GEO, "year"], how="inner").rename(columns={GEO: "geo"})
df["travellers_m"] = df["pop"] * df["part_pct"] / 100 / 1e6
df = df.dropna(subset=["travellers_m"]).sort_values(["geo", "year"]).reset_index(drop=True)

# 4) sanity check against the published ~65% EU participation for 2023
eu = df[df["geo"] == "EU27_2020"].copy()
eu["pop_m"] = eu["pop"] / 1e6
print(eu[["year", "part_pct", "pop_m", "travellers_m"]].round(1).to_string(index=False))
chk = eu[eu["year"] == 2023]
if len(chk):
    print("2023 EU27 participation %:", round(float(chk["part_pct"].iloc[0]), 1), "(expect about 65)")

# 5) country-level table (aggregates excluded) for a Europe-wide floor
countries = df[~df["geo"].str.startswith(("EU", "EA"))]
latest = countries.sort_values("year").groupby("geo").tail(1)
print("Countries:", len(latest), "| latest-year travellers sum (M):", round(latest["travellers_m"].sum(), 1))

# 6) save outputs
eu_out = eu[["year", "part_pct", "pop_m", "travellers_m"]].round(3)
eu_out.to_csv(f"{OUT_DIR}/eurostat_eu27_travellers.csv", index=False)
countries.round(3).to_csv(f"{OUT_DIR}/eurostat_country_travellers.csv", index=False)
print("Saved:", f"{OUT_DIR}/eurostat_eu27_travellers.csv", "and", f"{OUT_DIR}/eurostat_country_travellers.csv")


eu = pd.read_csv(f"{OUT_DIR}/eurostat_eu27_travellers.csv")
ctry = pd.read_csv(f"{OUT_DIR}/eurostat_country_travellers.csv")

# 1) EU27 travellers over time, with the COVID dip marked
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(eu["year"], eu["travellers_m"], marker="o", color="#2a7fff")
ax.axvspan(2019.5, 2021.5, color="grey", alpha=0.15, label="COVID years")
ax.set(title="EU27 travellers (1+ night trips), population aged 15+",
       xlabel="Year", ylabel="Travellers (millions)")
ax.legend()
fig.tight_layout(); fig.savefig(f"{PLOT_OUT}/eu27_travellers.png", dpi=150); plt.close(fig)

# 2) EU27 participation rate vs population base
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(eu["year"], eu["part_pct"], marker="o", color="#ff7a2a")
ax.set(title="EU27 participation in tourism (% of population 15+)",
       xlabel="Year", ylabel="Participation (%)")
fig.tight_layout(); fig.savefig(f"{PLOT_OUT}/eu27_participation.png", dpi=150); plt.close(fig)

# 3) top 15 countries by travellers, latest year per country
latest = ctry.sort_values("year").groupby("geo").tail(1)
top = latest.sort_values("travellers_m", ascending=False).head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(top["geo"] + " (" + top["year"].astype(str) + ")", top["travellers_m"], color="#2a7fff")
ax.set(title="Top 15 countries by travellers (latest available year)", xlabel="Travellers (millions)")
fig.tight_layout(); fig.savefig(f"{PLOT_OUT}/top_countries_travellers.png", dpi=150); plt.close(fig)

# 4) participation rate for selected countries (NL, FR, DE, ES, IT)
sel = ctry[ctry["geo"].isin(["NL", "FR", "DE", "ES", "IT"])]
fig, ax = plt.subplots(figsize=(8, 4.5))
for g, d in sel.groupby("geo"):
    ax.plot(d["year"], d["part_pct"], marker="o", label=g)
ax.set(title="Participation rate, selected countries (% of population 15+)",
       xlabel="Year", ylabel="Participation (%)")
ax.legend()
fig.tight_layout(); fig.savefig(f"{PLOT_OUT}/participation_selected.png", dpi=150); plt.close(fig)

print("Saved 4 charts to", PLOT_OUT)