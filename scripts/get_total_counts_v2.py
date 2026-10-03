"""
Get Total Available BioSample Counts v2 (with Date Filter)
Query NCBI BioSample for total record counts across 3 pathogens and 4 countries
using esearch with retmax=0 and publication date filter 2015/01/01 to 2025/12/31.
"""

import time
import os
import pandas as pd
from Bio import Entrez

Entrez.email = os.environ.get("NCBI_EMAIL", "your_email@example.com")
Entrez.api_key = os.environ.get("NCBI_API_KEY")

PATHOGENS = ["Escherichia coli", "Klebsiella pneumoniae", "Salmonella"]
COUNTRIES = ["Pakistan", "India", "Bangladesh", "United Kingdom"]
DELAY = 0.11


def get_total_count(organism, country, max_retries=3):
    term = f'"{organism}"[Organism] AND "{country}"[All Fields] AND ("2015/01/01"[PDAT] : "2025/12/31"[PDAT])'
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
                raise e


def main():
    rows = []
    print(f"{'Pathogen':<25} | {'Country':<16} | {'Total Available Count':>21}")
    print("-" * 68)

    for pathogen in PATHOGENS:
        for country in COUNTRIES:
            count = get_total_count(pathogen, country)
            rows.append({
                "pathogen": pathogen,
                "country": country,
                "total_available_count": count
            })
            print(f"{pathogen:<25} | {country:<16} | {count:>21,}")

    df = pd.DataFrame(rows)
    output_file = "outputs/total_counts_summary_v2.csv"
    df.to_csv(output_file, index=False)
    print("-" * 68)
    total_all = df["total_available_count"].sum()
    print(f"{'Total across all combinations':<44} | {total_all:>21,}")
    print(f"\nSaved summary to {output_file}")


if __name__ == "__main__":
    main()
