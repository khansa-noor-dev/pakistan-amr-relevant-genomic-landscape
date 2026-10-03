# Data files

`raw_snapshot/full_extraction_results_v2.csv` is the 6,000-record capped BioSample extraction used for this study.

`processed/full_extraction_results_v2_dated.csv` contains the 4,655 records passing post-retrieval collection-date eligibility. The corresponding undated and out-of-range records are retained for sample-flow reproducibility.

`processed/sectoral_breakdown_primary_conservative.csv` contains the primary conservative sector classification. Laboratory/reference records remain tagged in this file but are excluded from the analytical cohort (final N=4,542).

`processed/sectoral_breakdown_sensitivity_inference.csv` is the Typhi/Paratyphi inference sensitivity classification.

The files are snapshots of public NCBI BioSample metadata used in the analysis. NCBI is dynamic, so rerunning live queries at a later date may return different counts or ordering.
