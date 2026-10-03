import pandas as pd


COUNTS_FILE = "outputs/total_counts_summary_v2.csv"
POPULATION_FILE = "outputs/population_denominators_2024.csv"
OUTPUT_FILE = "outputs/table2_per_million_reproducible.csv"


def main():
    counts = pd.read_csv(COUNTS_FILE)
    populations = pd.read_csv(POPULATION_FILE)

    merged = counts.merge(
        populations[["country", "population_2024"]],
        on="country",
        how="left",
        validate="many_to_one",
    )
    if merged["population_2024"].isna().any():
        missing = merged.loc[merged["population_2024"].isna(), "country"].unique()
        raise ValueError(f"Missing population denominator(s): {missing}")

    merged["records_per_million"] = (
        merged["total_available_count"] / merged["population_2024"] * 1_000_000
    ).round(2)

    output = merged[
        [
            "pathogen",
            "country",
            "total_available_count",
            "population_2024",
            "records_per_million",
        ]
    ]
    output.to_csv(OUTPUT_FILE, index=False)

    table = output.pivot(
        index="pathogen", columns="country", values="records_per_million"
    )
    table = table[["Pakistan", "India", "Bangladesh", "United Kingdom"]]
    print(table.to_string())


if __name__ == "__main__":
    main()
