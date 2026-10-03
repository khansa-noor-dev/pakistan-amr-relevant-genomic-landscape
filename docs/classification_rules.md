# Sector classification rules

The manuscript's **primary analysis is conservative and does not use biology-based serovar inference**.

Order of classification:

1. Laboratory/reference markers in `organism` or `isolation_source` are tagged `Laboratory/Reference` and excluded from analytical sector percentages.
2. If `host` has usable content, precedence is Human -> Environmental -> Animal. Any other non-empty unmatched host is classified as Animal, matching the implemented analysis.
3. If host is unavailable, `isolation_source` precedence is Environmental -> Food/Plant -> Human -> Animal.
4. Otherwise the record is Unclassified.

The sensitivity analysis uses the same rules but additionally classifies records with both host and isolation source unavailable as Human when the organism string contains `typhi` or `paratyphi`.

The complete keyword lists are preserved in `scripts/sectoral_classification_v3_no_inference.py` and `scripts/sectoral_classification_v3.py`.
