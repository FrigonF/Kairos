import polars as pl
from pathlib import Path

INPUT = Path("data/raw/ais/ais-2025-01-08.csv")
OUTPUT = Path("data/processed/ais_clean.parquet")

print("Reading AIS data...")

df = (
    pl.scan_csv(
        INPUT,
        try_parse_dates=False,
        infer_schema_length=10000,
        ignore_errors=True,
    )
    .select([
        "mmsi",
        "base_date_time",
        "longitude",
        "latitude",
        "sog",
        "cog",
        "heading",
        "vessel_name",
        "imo",
        "call_sign",
        "vessel_type",
        "status",
        "length",
        "width",
        "draft",
        "cargo",
        "transceiver",
    ])
    .with_columns([
        pl.col("mmsi").cast(pl.Int64, strict=False),
        pl.col("base_date_time").str.strptime(
            pl.Datetime,
            "%Y-%m-%d %H:%M:%S",
            strict=False
        ),
        pl.col("longitude").cast(pl.Float64, strict=False),
        pl.col("latitude").cast(pl.Float64, strict=False),
        pl.col("sog").cast(pl.Float64, strict=False),
        pl.col("cog").cast(pl.Float64, strict=False),
        pl.col("heading").cast(pl.Float64, strict=False),
        pl.col("vessel_type").cast(pl.Int64, strict=False),
    ])
    .filter(
        pl.col("mmsi").is_not_null()
        & pl.col("base_date_time").is_not_null()
        & pl.col("longitude").is_between(-180, 180)
        & pl.col("latitude").is_between(-90, 90)
    )
)

print("Cleaning and writing Parquet...")

df.collect(streaming=True).write_parquet(
    OUTPUT,
    compression="zstd"
)

print(f"Done! Clean AIS saved to: {OUTPUT}")

import polars as pl
from pathlib import Path

INPUT = Path("data/raw/ais/ais-2025-01-08.csv")
OUTPUT = Path("data/processed/ais_clean.parquet")

print("Reading AIS data...")

df = (
    pl.scan_csv(
        INPUT,
        try_parse_dates=False,
        infer_schema_length=10000,
        ignore_errors=True,
    )
    .select([
        "mmsi",
        "base_date_time",
        "longitude",
        "latitude",
        "sog",
        "cog",
        "heading",
        "vessel_name",
        "imo",
        "call_sign",
        "vessel_type",
        "status",
        "length",
        "width",
        "draft",
        "cargo",
        "transceiver",
    ])
    .with_columns([
        pl.col("mmsi").cast(pl.Int64, strict=False),
        pl.col("base_date_time").str.strptime(
            pl.Datetime,
            "%Y-%m-%d %H:%M:%S",
            strict=False
        ),
        pl.col("longitude").cast(pl.Float64, strict=False),
        pl.col("latitude").cast(pl.Float64, strict=False),
        pl.col("sog").cast(pl.Float64, strict=False),
        pl.col("cog").cast(pl.Float64, strict=False),
        pl.col("heading").cast(pl.Float64, strict=False),
        pl.col("vessel_type").cast(pl.Int64, strict=False),
    ])
    .filter(
        pl.col("mmsi").is_not_null()
        & pl.col("base_date_time").is_not_null()
        & pl.col("longitude").is_between(-180, 180)
        & pl.col("latitude").is_between(-90, 90)
    )
)

print("Cleaning and writing Parquet...")

df.collect(streaming=True).write_parquet(
    OUTPUT,
    compression="zstd"
)

print(f"Done! Clean AIS saved to: {OUTPUT}")

