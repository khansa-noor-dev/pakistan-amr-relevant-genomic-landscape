"""
Get True Yearly BioSample Totals (2015-2025)
Runs esearch with retmax=0 for 3 pathogens x 4 countries x 11 years (132 queries)
using publication date filter: AND ("YYYY/01/01"[PDAT] : "YYYY/12/31"[PDAT]).

Output:
    true_yearly_totals.csv - columns: pathogen, country, year, true_total_count
"""

import time
import os
import pandas as pd
from Bio import Entrez

Entrez.email = os.environ.get("NCBI_EMAIL", "your_email@example.com")
Entrez.api_key = os.environ.get("NCBI_API_KEY")

PATHOGENS = ["Escherichia coli", "Klebsiella pneumoniae", "Salmonella"]
COUNTRIES = ["Pakistan", "India", "Bangladesh", "United Kingdom"]
YEARS = list(range(2015, 2026))  # 2015 through 2025
DELAY = 0.11  # safely under the 10 requests/sec limit


def get_yearly_count(organism, country, year, max_retries=3):
    term = f'"{organism}"[Organism] AND "{country}"[All Fields] AND ("{year}/01/01"[PDAT] : "{year}/12/31"[PDAT])'
    for attempt in range(max_retries):
        try:
            time.sleep(DELAY)
            handle = Entrez.esearch(db="biosample", term=term, retmax=0)
            record = Entrez.read(handle)
            handle.close()
            return int(record["Count"])
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"Error for {organism} + {country} + {year}: {e}", flush=True)
                raise e


def main():
    rows = []
    total_queries = len(PATHOGENS) * len(COUNTRIES) * len(YEARS)
    print(f"Starting {total_queries} queries (3 pathogens x 4 countries x 11 years)...\n", flush=True)

    query_num = 0
    start_time = time.time()

    for pathogen in PATHOGENS:
        for country in COUNTRIES:
            for year in YEARS:
                query_num += 1
                count = get_yearly_count(pathogen, country, year)
                rows.append({
                    "pathogen": pathogen,
                    "country": country,
                    "year": year,
                    "true_total_count": count
                })
                if query_num % 11 == 0:
                    elapsed = time.time() - start_time
                    print(f"[{query_num:3d}/{total_queries}] Completed {pathogen} - {country} (Elapsed: {elapsed:.1f}s)", flush=True)

    df = pd.DataFrame(rows)
    output_file = "outputs/true_yearly_totals.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved all results to {output_file}", flush=True)

    # Display Year x Country Totals (summed across pathogens)
    pivot = df.pivot_table(index="year", columns="country", values="true_total_count", aggfunc="sum")
    # Order columns
    country_order = ["Bangladesh", "India", "Pakistan", "United Kingdom"]
    pivot = pivot[country_order]
    pivot["Total"] = pivot.sum(axis=1)

    print("\n" + "=" * 70)
    print("TRUE YEARLY TOTALS: YEAR x COUNTRY (Summed across all 3 pathogens)")
    print("=" * 70)
    print(pivot)

    # Total across all years
    totals_row = pivot.sum(axis=0)
    totals_row.name = "All Years (2015-2025)"
    print("-" * 70)
    print(pd.DataFrame([totals_row]).to_string(index=True))


if __name__ == "__main__":
    main()
