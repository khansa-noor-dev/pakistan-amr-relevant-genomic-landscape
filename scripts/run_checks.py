"""
Script to execute Checks 1 and 2 on full_extraction_results_v2_dated.csv:
1. Unique BioProjects per combination, top BioProject share, and >30% dominance flags.
2. Quality classification (Missing/Malformed/Valid) overall and by country on the 4,542
   non-lab surveillance records.
"""

import time
import os
import re
import pandas as pd
import numpy as np
from Bio import Entrez
import xml.etree.ElementTree as ET

Entrez.email = os.environ.get("NCBI_EMAIL", "your_email@example.com")
Entrez.api_key = os.environ.get("NCBI_API_KEY")
DELAY = 0.11

INPUT_FILE = "data/processed/full_extraction_results_v2_dated.csv"
OUTPUT_WITH_BIOPROJECT = "data/processed/full_extraction_results_v2_dated_with_bioproject.csv"


def fetch_bioprojects(biosample_ids, batch_size=200, max_retries=3):
    """Fetch BioProject accessions for given BioSample IDs."""
    mapping = {}
    total = len(biosample_ids)
    print(f"Fetching BioProjects for {total} BioSamples in batches of {batch_size}...", flush=True)

    for idx in range(0, total, batch_size):
        chunk = [str(x) for x in biosample_ids[idx:idx + batch_size]]
        root = None
        for attempt in range(max_retries):
            time.sleep(DELAY)
            try:
                handle = Entrez.efetch(db="biosample", id=chunk, rettype="full", retmode="xml")
                xml_data = handle.read()
                handle.close()
                root = ET.fromstring(xml_data)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"Error fetching batch at {idx}: {e}", flush=True)

        if root is not None:
            for bs in root.findall(".//BioSample"):
                bs_id = int(bs.get("id"))
                proj = None
                for link in bs.findall(".//Links/Link"):
                    if link.get("target") == "bioproject":
                        proj = link.get("label") or link.text
                        break
                mapping[bs_id] = proj

        fetched = min(idx + batch_size, total)
        print(f"  ...{fetched}/{total} BioSamples processed", flush=True)

    return mapping


def classify_field(value, field_name):
    """Classify a field's value as Missing, Malformed, or Valid."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return "Missing"

    v = str(value).strip().lower()
    malformed_markers = [
        "not provided", "not applicable", "missing", "n/a", "unknown", "not available", "-"
    ]
    if v in malformed_markers:
        return "Malformed"

    if field_name == "geo_loc_name" and ("asia" in v or "europe" in v or "africa" in v) and ":" in v:
        return "Malformed"

    return "Valid"


LAB_STRAIN_MARKERS = [
    "k-12", "mg1655", "cell pellet", "induced conditions", "reference strain",
    "laboratory strain"
]


def matches_any(value, keywords):
    return any(k in str(value).lower() for k in keywords)


def main():
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df)} records from {INPUT_FILE}\n")

    # -------------------------------------------------------------
    # PART 1: BIOPROJECT ANALYSIS
    # -------------------------------------------------------------
    bioproject_map = fetch_bioprojects(df["biosample_id"].tolist())
    df["bioproject_accession"] = df["biosample_id"].map(bioproject_map)
    df.to_csv(OUTPUT_WITH_BIOPROJECT, index=False)
    print(f"Saved dataset with BioProject accessions to {OUTPUT_WITH_BIOPROJECT}\n")

    rows_bp = []
    combos = df.groupby(["search_pathogen", "search_country"])

    for (pathogen, country), group in combos:
        total_sample = len(group)
        unique_bp = group["bioproject_accession"].dropna().nunique()
        missing_bp = group["bioproject_accession"].isna().sum()

        top_bp = None
        top_count = 0
        top_share = 0.0

        vc = group["bioproject_accession"].value_counts()
        if len(vc) > 0:
            top_bp = vc.index[0]
            top_count = vc.iloc[0]
            top_share = (top_count / total_sample) * 100

        flag = "FLAG (>30%)" if top_share > 30.0 else "OK"

        rows_bp.append({
            "Pathogen": pathogen,
            "Country": country,
            "Sample Size": total_sample,
            "Unique BioProjects": unique_bp,
            "Top BioProject": top_bp,
            "Top BioProject Count": top_count,
            "Top BioProject Share (%)": round(top_share, 1),
            "Status": flag
        })

    df_bp_summary = pd.DataFrame(rows_bp)
    print("=" * 80)
    print("CHECK 1: BIOPROJECT UNIQUE COUNTS AND DOMINANCE ASSESSMENT")
    print("=" * 80)
    print(df_bp_summary.to_string(index=False))

    # -------------------------------------------------------------
    # PART 2: QUALITY CLASSIFICATION ON SURVEILLANCE RECORDS
    # -------------------------------------------------------------
    # Exclude 113 Laboratory/Reference records
    is_lab = df.apply(
        lambda r: matches_any(r.get("organism", ""), LAB_STRAIN_MARKERS) or
                  matches_any(r.get("isolation_source", ""), LAB_STRAIN_MARKERS),
        axis=1
    )
    print(f"\nExcluding {is_lab.sum()} Laboratory/Reference records...")
    df_surv = df[~is_lab].copy()
    print(f"Surveillance cohort size: {len(df_surv)} records\n")

    # Recompute quality flags
    df_surv["geo_loc_name_quality"] = df_surv["geo_loc_name"].apply(lambda v: classify_field(v, "geo_loc_name"))
    df_surv["isolation_source_quality"] = df_surv["isolation_source"].apply(lambda v: classify_field(v, "isolation_source"))
    df_surv["host_quality"] = df_surv["host"].apply(lambda v: classify_field(v, "host"))

    fields = ["geo_loc_name", "isolation_source", "host"]

    print("=" * 80)
    print("CHECK 2A: OVERALL QUALITY CLASSIFICATION PERCENTAGES (N = 4,542)")
    print("=" * 80)
    overall_rows = []
    for f in fields:
        col = f + "_quality"
        counts = df_surv[col].value_counts()
        valid_cnt = counts.get("Valid", 0)
        malf_cnt = counts.get("Malformed", 0)
        miss_cnt = counts.get("Missing", 0)
        tot = len(df_surv)

        overall_rows.append({
            "Field": f,
            "Valid (%)": f"{valid_cnt / tot * 100:.1f}% ({valid_cnt:,})",
            "Malformed (%)": f"{malf_cnt / tot * 100:.1f}% ({malf_cnt:,})",
            "Missing (%)": f"{miss_cnt / tot * 100:.1f}% ({miss_cnt:,})"
        })
    print(pd.DataFrame(overall_rows).to_string(index=False))

    print("\n" + "=" * 80)
    print("CHECK 2B: QUALITY CLASSIFICATION BREAKDOWN BY COUNTRY (%)")
    print("=" * 80)
    countries = ["Bangladesh", "India", "Pakistan", "United Kingdom"]

    for f in fields:
        col = f + "_quality"
        print(f"\n--- Field: {f} ---")
        ct = pd.crosstab(df_surv["search_country"], df_surv[col], normalize="index") * 100
        ct_cnt = pd.crosstab(df_surv["search_country"], df_surv[col])
        for q in ["Valid", "Malformed", "Missing"]:
            if q not in ct.columns:
                ct[q] = 0.0
        ct = ct[["Valid", "Malformed", "Missing"]].round(1)
        print(ct)


if __name__ == "__main__":
    main()
