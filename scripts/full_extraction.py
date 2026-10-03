"""
Full-Scale Extraction Script - Step 4
Purpose: Extract BioSample metadata for 3 pathogens across 4 countries
(Pakistan, India, Bangladesh, UK), with quality classification applied
to key fields.

IMPORTANT: Set NCBI_EMAIL and optionally NCBI_API_KEY as environment variables before running.

Usage:
    python full_extraction.py

Output:
    full_extraction_results.csv - all extracted records, one row per isolate,
    with quality flags already applied.
"""

import time
import os
import pandas as pd
from Bio import Entrez
from xml.etree import ElementTree as ET

# ---- CONFIG ----
Entrez.email = os.environ.get("NCBI_EMAIL", "your_email@example.com")
Entrez.api_key = os.environ.get("NCBI_API_KEY")

PATHOGENS = ["Escherichia coli", "Klebsiella pneumoniae", "Salmonella"]
COUNTRIES = ["Pakistan", "India", "Bangladesh", "United Kingdom"]
MAX_RECORDS_PER_COMBO = 500   # cap per pathogen+country combo, adjust if needed
DELAY = 0.11                  # ~9 requests/sec, safely under the 10/sec API-key limit


def search_biosamples(organism, country, retmax, max_retries=3):
    """Search NCBI BioSample for organism + country, return list of BioSample IDs."""
    term = f'"{organism}"[Organism] AND "{country}"[All Fields] AND ("2015/01/01"[PDAT] : "2025/12/31"[PDAT])'
    for attempt in range(max_retries):
        try:
            handle = Entrez.esearch(db="biosample", term=term, retmax=retmax)
            record = Entrez.read(handle)
            handle.close()
            return record["IdList"]
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"  Error searching biosamples: {e}", flush=True)
                return []



def classify_field(value, field_name):
    """Classify a field's value as Missing, Malformed, or Valid."""
    if value is None or str(value).strip() == "":
        return "Missing"

    v = str(value).strip().lower()

    malformed_markers = ["not provided", "not applicable", "missing", "n/a", "unknown", "not available"]
    if v in malformed_markers:
        return "Malformed"

    if field_name == "geo_loc_name" and ("asia" in v or "europe" in v or "africa" in v) and ":" in v:
        # continent name appearing where a country/region is expected
        return "Malformed"

    return "Valid"


def fetch_biosample_details(id_list, pathogen, country, batch_size=100, max_retries=3):
    """Fetch and parse BioSample records for given IDs in batches."""
    results = []
    total = len(id_list)
    for idx in range(0, total, batch_size):
        chunk = id_list[idx:idx + batch_size]
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
                    print(f"  Batch error: {e}", flush=True)

        if root is None:
            for biosample_id in chunk:
                results.append({
                    "search_pathogen": pathogen, "search_country": country,
                    "biosample_id": biosample_id, "error": "Fetch failed"
                })
            continue

        biosample_elems = root.findall(".//BioSample")
        for bs in biosample_elems:
            try:
                record = {
                    "search_pathogen": pathogen,
                    "search_country": country,
                    "biosample_id": bs.get("id"),
                    "accession": bs.get("accession"),
                    "organism": None,
                    "geo_loc_name": None,
                    "isolation_source": None,
                    "collection_date": None,
                    "host": None,
                    "host_disease": None,
                    "genotype": None,
                }

                organism_elem = bs.find(".//Organism")
                if organism_elem is not None:
                    record["organism"] = organism_elem.get("taxonomy_name")

                for attr in bs.findall(".//Attribute"):
                    name = attr.get("attribute_name", "").lower()
                    harmonized = attr.get("harmonized_name", "").lower()
                    value = attr.text
                    key = harmonized or name

                    if "geo_loc_name" in key:
                        record["geo_loc_name"] = value
                    elif "isolation_source" in key:
                        record["isolation_source"] = value
                    elif "collection_date" in key:
                        record["collection_date"] = value
                    elif key == "host":
                        record["host"] = value
                    elif "host_disease" in key or "host disease" in name:
                        record["host_disease"] = value
                    elif "genotype" in key:
                        record["genotype"] = value

                # quality classification
                record["geo_loc_name_quality"] = classify_field(record["geo_loc_name"], "geo_loc_name")
                record["isolation_source_quality"] = classify_field(record["isolation_source"], "isolation_source")
                record["host_quality"] = classify_field(record["host"], "host")

                results.append(record)

            except Exception as e:
                results.append({
                    "search_pathogen": pathogen, "search_country": country,
                    "biosample_id": bs.get("id"), "error": str(e)
                })

        fetched_so_far = min(idx + batch_size, total)
        print(f"  ...{fetched_so_far}/{total} fetched", flush=True)

    return results


def main():
    all_records = []

    for pathogen in PATHOGENS:
        for country in COUNTRIES:
            print(f"\nSearching: {pathogen} + {country}", flush=True)
            id_list = search_biosamples(pathogen, country, MAX_RECORDS_PER_COMBO)
            print(f"  Found {len(id_list)} records. Fetching details...", flush=True)

            if not id_list:
                continue

            records = fetch_biosample_details(id_list, pathogen, country)
            all_records.extend(records)

    df = pd.DataFrame(all_records)
    output_path = "data/raw_snapshot/full_extraction_results_v2.csv"
    df.to_csv(output_path, index=False)

    print(f"\n\nDONE. {len(df)} total records saved to {output_path}", flush=True)
    print("\n--- SUMMARY BY PATHOGEN + COUNTRY ---", flush=True)
    if "search_pathogen" in df.columns:
        print(df.groupby(["search_pathogen", "search_country"]).size(), flush=True)

    print("\n--- QUALITY FLAG SUMMARY ---", flush=True)
    for col in ["geo_loc_name_quality", "isolation_source_quality", "host_quality"]:
        if col in df.columns:
            print(f"\n{col}:", flush=True)
            print(df[col].value_counts(dropna=False), flush=True)


if __name__ == "__main__":
    main()

