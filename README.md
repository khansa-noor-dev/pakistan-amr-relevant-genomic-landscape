# Genomic Data Landscape of AMR-Relevant Bacterial Pathogens in Pakistan

Reproducibility package for the manuscript comparing public NCBI BioSample representation of *Escherichia coli*, *Klebsiella pneumoniae*, and *Salmonella* across Pakistan, India, Bangladesh, and the United Kingdom for 2015-2025.

## Study scope

The study analyzes **genomic data for AMR-relevant bacterial pathogens**, not a dataset restricted to AMR-confirmed isolates. BioSample records were retrieved by organism, country, and publication-date (PDAT) criteria. The analysis therefore measures public-repository representation and should not be interpreted as national AMR prevalence or complete surveillance activity.

## Repository snapshot

Final NCBI query outputs underlying the manuscript were generated on **25 September 2026**. The capped extraction used up to 500 records per pathogen-country combination in NCBI default result order. Because NCBI is dynamic, later live reruns may differ from the archived study snapshot.

## Query template

    "<organism>"[Organism] AND "<country>"[All Fields] AND ("2015/01/01"[PDAT] : "2025/12/31"[PDAT])

## Main sample flow

- 6,000 capped BioSample records retrieved across 12 pathogen-country combinations.
- 4,655 records passed post-retrieval `collection_date` eligibility.
- 113 laboratory/reference records were excluded from the analytical cohort.
- Final analytical sample: **N = 4,542**.

Accepted single collection-date forms were `YYYY`, `YYYY-MM`, and `YYYY-MM-DD`. Date ranges were retained only when both endpoint years were within 2015-2025. Missing, placeholder/unparseable, and out-of-range dates were excluded from the date-valid dataset.

## Directory structure

- `scripts/` - extraction, filtering, classification, repository-count, BioProject/metadata, per-capita, and final statistical reproduction scripts.
- `data/raw_snapshot/` - archived 6,000-record extraction used by the study.
- `data/processed/` - date-filtered and classified analysis datasets.
- `outputs/` - final summary/count outputs used in the manuscript.
- `docs/` - classification documentation.

Historical pilot files, superseded scripts, manuscript drafts, and obsolete repository-count outputs are intentionally excluded.

## Setup

Python 3.10+ is recommended.

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt

For live NCBI queries, set credentials as environment variables rather than editing scripts:

    NCBI_EMAIL=your_email@example.com
    NCBI_API_KEY=your_ncbi_api_key_here

The API key is optional for Entrez but enables a higher request rate. Never commit a real API key.

## Reproducing the archived analysis

To reproduce analyses from the archived study snapshot without making live NCBI queries:

    python scripts/sectoral_classification_v3_no_inference.py
    python scripts/sectoral_classification_v3.py
    python scripts/calculate_table2_per_million.py
    python scripts/reproduce_final_statistics.py

The scripts inherited from the study use file names relative to their working directory. The archived outputs are included so the exact manuscript snapshot remains inspectable even if NCBI changes later.

## Live data retrieval

The following scripts query NCBI and can produce different values when rerun after the study retrieval date:

- `full_extraction.py`
- `get_total_counts_v2.py`
- `get_true_yearly_totals.py`
- `run_checks.py` (BioProject lookup)

## Primary vs sensitivity sector analysis

`sectoral_classification_v3_no_inference.py` is the **primary conservative classification** used for the main sector analysis. `sectoral_classification_v3.py` is the sensitivity analysis that adds Typhi/Paratyphi biology-based inference when host and isolation-source metadata are unavailable. See `docs/classification_rules.md`.

## Population denominators

Per-capita calculations use 2024 World Bank population values stored in `outputs/population_denominators_2024.csv`. The archived denominator file includes the indicator, retrieval date, and source endpoint used for verification.

## Citation

Citation metadata are provided in `CITATION.cff`. After archival in Zenodo, add the Zenodo DOI to this README and to the manuscript Data and Code Availability statement.

## License

Code in this repository is released under the MIT License. Public-source metadata remain subject to the terms and policies of their originating databases.
