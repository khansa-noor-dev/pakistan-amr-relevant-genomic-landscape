"""
Filter Full Extraction Results v2 by Collection Date (2015-2025)

Filters full_extraction_results_v2.csv into:
1. full_extraction_results_v2_dated.csv: records with collection_date within 2015-2025
2. full_extraction_results_v2_undated.csv: records with missing or uninformative collection_date
3. full_extraction_results_v2_out_of_range.csv: records with collection_date outside 2015-2025 (< 2015 or > 2025)
"""

import re
import pandas as pd

INPUT_FILE = "data/raw_snapshot/full_extraction_results_v2.csv"
OUTPUT_DATED = "data/processed/full_extraction_results_v2_dated.csv"
OUTPUT_UNDATED = "data/processed/full_extraction_results_v2_undated.csv"
OUTPUT_OUT_OF_RANGE = "data/processed/full_extraction_results_v2_out_of_range.csv"

INVALID_DATE_STRINGS = {
    "", "nan", "none", "not applicable", "not provided", "missing",
    "not collected", "unknown", "n/a", "na", "-"
}


def classify_collection_date(date_val):
    if pd.isna(date_val):
        return "undated", None

    d_str = str(date_val).strip()
    if d_str.lower() in INVALID_DATE_STRINGS:
        return "undated", None

    # Check date range: YYYY/YYYY, YYYY-MM/YYYY-MM, etc.
    m_range = re.match(
        r"^(\d{4})(?:-\d{2})?(?:-\d{2})?/(\d{4})(?:-\d{2})?(?:-\d{2})?$",
        d_str
    )
    if m_range:
        y1, y2 = int(m_range.group(1)), int(m_range.group(2))
        if 2015 <= y1 <= 2025 and 2015 <= y2 <= 2025:
            return "dated_in_range", (y1, y2)
        else:
            return "out_of_range", (y1, y2)

    # Check single date: YYYY, YYYY-MM, YYYY-MM-DD
    m_single = re.match(r"^(\d{4})(?:-\d{2})?(?:-\d{2})?$", d_str)
    if m_single:
        y = int(m_single.group(1))
        if 2015 <= y <= 2025:
            return "dated_in_range", (y, y)
        else:
            return "out_of_range", (y, y)

    return "undated", None


def main():
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df)} records from {INPUT_FILE}")

    statuses = []
    for d in df["collection_date"]:
        status, _ = classify_collection_date(d)
        statuses.append(status)

    df["_date_status"] = statuses

    # 1. Dated records within 2015-2025
    df_dated = df[df["_date_status"] == "dated_in_range"].drop(columns=["_date_status"])
    df_dated.to_csv(OUTPUT_DATED, index=False)
    print(f"Saved {len(df_dated)} dated records (2015-2025) to {OUTPUT_DATED}")

    # 2. Undated records (missing / uninformative)
    df_undated = df[df["_date_status"] == "undated"].drop(columns=["_date_status"])
    df_undated.to_csv(OUTPUT_UNDATED, index=False)
    print(f"Saved {len(df_undated)} undated records to {OUTPUT_UNDATED}")

    # 3. Out-of-range records (< 2015 or > 2025)
    df_out_of_range = df[df["_date_status"] == "out_of_range"].drop(columns=["_date_status"])
    df_out_of_range.to_csv(OUTPUT_OUT_OF_RANGE, index=False)
    print(f"Saved {len(df_out_of_range)} out-of-range records to {OUTPUT_OUT_OF_RANGE}")

    # Summary table
    print("\n" + "=" * 65)
    print("FINAL RECORD COUNT PER PATHOGEN + COUNTRY (2015-2025 DATED)")
    print("=" * 65)
    summary = (
        df_dated.groupby(["search_pathogen", "search_country"])
        .size()
        .reset_index(name="count_dated")
    )
    print(summary.to_string(index=False))

    print("\n" + "=" * 65)
    print("CROSS-TABULATION")
    print("=" * 65)
    pivot = pd.crosstab(df_dated["search_pathogen"], df_dated["search_country"])
    print(pivot)

    # Flag check: < 100 records
    print("\n" + "=" * 65)
    print("CHECKING FOR COMBINATIONS WITH < 100 RECORDS")
    print("=" * 65)
    low_combos = summary[summary["count_dated"] < 100]
    if len(low_combos) == 0:
        print("All 12 combinations have at least 100 records!")
    else:
        print(f"WARNING: Found {len(low_combos)} combination(s) with < 100 records:")
        print(low_combos.to_string(index=False))


if __name__ == "__main__":
    main()
