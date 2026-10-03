"""
Sectoral Classification Script v3 - Sensitivity Analysis (Typhi/Paratyphi Inference)
Changes from v2:
  - New rule: Salmonella Typhi / Paratyphi A with empty host AND empty
    isolation_source are inferred as Human (human-restricted pathogens).
  - New "Food/Plant" sector for spices, produce, and plant-based commodities
    (kept separate from Environmental to avoid diluting water/soil/sewage signal).
  - New "Laboratory/Reference" tag for lab reference strains (e.g. K-12 MG1655) -
    these are EXCLUDED from sector percentage calculations entirely.
  - Expanded ANIMAL_KEYWORDS (tuna, tilapia, pork, raw milk, frog leg, farm feed)
  - Expanded ENV_KEYWORDS for built environment / retail / waste contexts
    (market, dumpsite, hospital surface, medical waste, microplastics)

Input:
    full_extraction_results_v2_dated.csv

Output:
    sectoral_breakdown_v3.csv - original data + 'sector' column (includes Laboratory/Reference)
    sectoral_summary_v3.csv - counts by pathogen x country x sector (lab strains excluded)
"""

import pandas as pd

INPUT_FILE = "data/processed/full_extraction_results_v2_dated.csv"
OUTPUT_DETAIL = "data/processed/sectoral_breakdown_sensitivity_inference.csv"
OUTPUT_SUMMARY = "outputs/sectoral_summary_sensitivity_inference.csv"

INVALID_VALUES = [
    "", "nan", "none", "not provided", "not applicable", "missing",
    "n/a", "na", "unknown", "not available", "-"
]

HUMAN_KEYWORDS = [
    "homo sapiens", "homosapiens", "human", "patient", "clinical",
    "h. sapiens", "man", "woman"
]

ENV_KEYWORDS = [
    "water", "soil", "sewage", "sediment", "environment", "drain",
    "effluent", "wastewater", "waste water", "river", "pond", "irrigation",
    "farm environment", "drinking water", "surface water", "manure",
    "compost", "sludge", "biofilm", "environmental",
    "market", "dumpsite", "hospital surface", "medical waste",
    "microplastic", "retail", "chopping board", "kitchen waste"
]

ANIMAL_KEYWORDS = [
    "chicken", "poultry", "cattle", "bovine", "swine", "pig", "goat",
    "sheep", "livestock", "meat", "shrimp", "fish", "duck", "turkey",
    "dairy", "broiler", "layer", "animal", "veterinary", "dog", "cat",
    "horse", "buffalo", "cloacal", "tuna", "tilapia", "pork",
    "raw milk", "frog", "farm feed"
]

HUMAN_SOURCE_KEYWORDS = [
    "stool", "urine", "feces", "faeces", "blood", "sputum", "wound",
    "csf", "pus", "throat", "nasal", "rectal swab", "human", "uti",
    "urinary tract", "surgical site", "catheter", "sepsis",
    "lung tissue", "heart tissue", "tissue"
]

FOOD_PLANT_KEYWORDS = [
    "moringa", "chilli", "chili", "coriander", "turmeric", "ginger",
    "sesame", "peanut", "mung bean", "vegetable", "salad", "seed",
    "spice", "powder", "produce", "leaf"
]

# Organism name fragments indicating human-restricted Salmonella serovars
HUMAN_RESTRICTED_SEROVARS = ["typhi", "paratyphi"]

# Phrases indicating a lab reference strain, not a field surveillance isolate
LAB_STRAIN_MARKERS = [
    "k-12", "mg1655", "cell pellet", "induced conditions", "reference strain",
    "laboratory strain"
]


def matches_any(value, keywords):
    return any(k in value for k in keywords)


def classify_sector(row):
    host = str(row.get("host", "")).strip().lower()
    source = str(row.get("isolation_source", "")).strip().lower()
    organism = str(row.get("organism", "")).strip().lower()

    host_is_invalid = host in INVALID_VALUES
    source_is_invalid = source in INVALID_VALUES

    # --- Rule 0: Lab reference strains - tagged and excluded from analysis ---
    if matches_any(organism, LAB_STRAIN_MARKERS) or matches_any(source, LAB_STRAIN_MARKERS):
        return "Laboratory/Reference"

    # --- Case A: host field has real content ---
    if not host_is_invalid:
        if matches_any(host, HUMAN_KEYWORDS):
            return "Human"
        if matches_any(host, ENV_KEYWORDS):
            return "Environmental"
        if matches_any(host, ANIMAL_KEYWORDS):
            return "Animal"
        return "Animal"  # unrecognized but non-empty host -> likely an animal species name

    # --- Case B: host empty, check isolation_source ---
    if not source_is_invalid:
        if matches_any(source, ENV_KEYWORDS):
            return "Environmental"
        if matches_any(source, FOOD_PLANT_KEYWORDS):
            return "Food/Plant"
        if matches_any(source, HUMAN_SOURCE_KEYWORDS):
            return "Human"
        if matches_any(source, ANIMAL_KEYWORDS):
            return "Animal"

    # --- Case C: both empty - check biology-based inference ---
    if host_is_invalid and source_is_invalid:
        if matches_any(organism, HUMAN_RESTRICTED_SEROVARS):
            return "Human"

    return "Unclassified"


def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} records from {INPUT_FILE}")

    df["sector"] = df.apply(classify_sector, axis=1)
    df.to_csv(OUTPUT_DETAIL, index=False)
    print(f"Full detail (including Laboratory/Reference) saved to {OUTPUT_DETAIL}")

    n_lab = (df["sector"] == "Laboratory/Reference").sum()
    print(f"\n{n_lab} records tagged as Laboratory/Reference and EXCLUDED from analysis below.")
    analysis_df = df[df["sector"] != "Laboratory/Reference"].copy()

    summary = (
        analysis_df.groupby(["search_pathogen", "search_country", "sector"])
        .size()
        .reset_index(name="count")
    )
    summary.to_csv(OUTPUT_SUMMARY, index=False)
    print(f"Summary (excluding lab strains) saved to {OUTPUT_SUMMARY}")

    print("\n--- OVERALL SECTOR DISTRIBUTION (excluding Laboratory/Reference) ---")
    print(analysis_df["sector"].value_counts())
    print(f"\nUnclassified remaining: {(analysis_df['sector'] == 'Unclassified').sum()} "
          f"({(analysis_df['sector'] == 'Unclassified').mean()*100:.1f}%)")

    print("\n--- SECTOR DISTRIBUTION BY COUNTRY (%) ---")
    pivot = pd.crosstab(analysis_df["search_country"], analysis_df["sector"], normalize="index") * 100
    print(pivot.round(1))

    print("\n--- SECTOR DISTRIBUTION BY PATHOGEN (%) ---")
    pivot2 = pd.crosstab(analysis_df["search_pathogen"], analysis_df["sector"], normalize="index") * 100
    print(pivot2.round(1))


if __name__ == "__main__":
    main()
