"""Reproduce the manuscript's final sector contingency tests and sensitivity shifts.
Uses saved final analysis outputs; does not query NCBI or alter source data.
"""
from pathlib import Path
import pandas as pd
from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "data/processed/sectoral_breakdown_primary_conservative.csv"
SENSITIVITY = ROOT / "data/processed/sectoral_breakdown_sensitivity_inference.csv"
OUT = ROOT / "outputs/final_statistical_summary.csv"
SECTORS = ["Human", "Animal", "Environmental", "Food/Plant", "Unclassified"]
COUNTRIES = ["Bangladesh", "India", "Pakistan", "United Kingdom"]

def analysis_cohort(path):
    df = pd.read_csv(path, low_memory=False)
    return df[df["sector"] != "Laboratory/Reference"].copy()

def cramers_v(chi2, n, r, c):
    return (chi2 / (n * min(r - 1, c - 1))) ** 0.5

def main():
    primary = analysis_cohort(PRIMARY)
    sensitivity = analysis_cohort(SENSITIVITY)
    table = pd.crosstab(primary["search_country"], primary["sector"]).reindex(index=COUNTRIES, columns=SECTORS, fill_value=0)
    chi2, p, dof, _ = chi2_contingency(table)
    v = cramers_v(chi2, table.to_numpy().sum(), *table.shape)

    robust = table.drop(columns=["Food/Plant"])
    chi2_r, p_r, dof_r, _ = chi2_contingency(robust)
    v_r = cramers_v(chi2_r, robust.to_numpy().sum(), *robust.shape)

    rows = [
        {"analysis":"primary_4x5","N":int(table.to_numpy().sum()),"chi_square":chi2,"df":dof,"p_value":p,"cramers_v":v},
        {"analysis":"food_plant_excluded_4x4","N":int(robust.to_numpy().sum()),"chi_square":chi2_r,"df":dof_r,"p_value":p_r,"cramers_v":v_r},
    ]
    pd.DataFrame(rows).to_csv(OUT, index=False)

    print(table)
    print(f"Primary: chi2={chi2:.6f}, df={dof}, p={p:.6g}, V={v:.6f}, N={table.to_numpy().sum()}")
    print(f"Robustness: chi2={chi2_r:.6f}, df={dof_r}, p={p_r:.6g}, V={v_r:.6f}, N={robust.to_numpy().sum()}")

    print("\nHuman-share sensitivity shifts (percentage points):")
    for country in COUNTRIES:
        p0 = primary[primary.search_country.eq(country)]
        ps = sensitivity[sensitivity.search_country.eq(country)]
        a = 100 * p0.sector.eq("Human").mean()
        b = 100 * ps.sector.eq("Human").mean()
        print(f"{country}: {a:.2f}% -> {b:.2f}% ({b-a:+.2f} pp)")

if __name__ == "__main__":
    main()
