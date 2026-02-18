# Databricks notebook source
# MAGIC %pip install polars nflreadpy
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Load configuration from setup notebook
import json
from pathlib import Path
CONFIG = json.loads(Path("config/dc_assistant.json").read_text())

# Extract configuration variables
CATALOG = CONFIG["workspace"]["catalog"]
SCHEMA = CONFIG["workspace"]["schema"]
SEASONS = CONFIG["data_collection"]["seasons"]

import polars as pl
import pandas as pd
import nflreadpy as nfl
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

print(f"Using catalog.schema: {CATALOG}.{SCHEMA}")
print(f"Target seasons: {SEASONS}")

# COMMAND ----------

# COMMAND ----------
# Load datasets via nflreadpy (returns Polars DataFrames)
print("Loading Play-by-Play...")
pbp_pl: pl.DataFrame = nfl.load_pbp(SEASONS)
print("PBP shape:", pbp_pl.shape)

print("Loading Participation...")
part_pl: pl.DataFrame = nfl.load_participation(SEASONS)
print("Participation shape:", part_pl.shape)

print("Loading Rosters and Teams...")
rosters_pl: pl.DataFrame = nfl.load_rosters(SEASONS)
teams_pl: pl.DataFrame = nfl.load_teams()
print("Rosters shape:", rosters_pl.shape, "Teams shape:", teams_pl.shape)

print("Loading Players (all available)...")
players_pl: pl.DataFrame = nfl.load_players()
print("Players shape:", players_pl.shape)

# COMMAND ----------
# Persist to Delta tables in Unity Catalog

def write_delta_from_polars(df_pl: pl.DataFrame, full_table_name: str) -> None:
    """Write a Polars DataFrame to a Delta table via Spark."""
    pdf: pd.DataFrame = df_pl.to_pandas()
    sdf = spark.createDataFrame(pdf)
    (sdf.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_table_name))
    print(f"Wrote table: {full_table_name}  (rows={sdf.count()})")

write_delta_from_polars(pbp_pl, f"{CATALOG}.{SCHEMA}.football_pbp")
write_delta_from_polars(part_pl, f"{CATALOG}.{SCHEMA}.football_participation")
write_delta_from_polars(rosters_pl, f"{CATALOG}.{SCHEMA}.football_rosters")
write_delta_from_polars(teams_pl, f"{CATALOG}.{SCHEMA}.football_teams")
write_delta_from_polars(players_pl, f"{CATALOG}.{SCHEMA}.football_players")

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS users.wesley_pasfield.football_pbp;

# COMMAND ----------

print("Loading Play-by-Play...")
COLUMN_TO_DROPs = ["lateral_sack_player_id", "lateral_sack_player_name", "tackle_for_loss_2_player_id", "tackle_for_loss_2_player_name", "st_play_type", "end_yard_line"]
pbp_pl: pl.DataFrame = nfl.load_pbp(SEASONS)
pbp_pl = pbp_pl.drop(COLUMN_TO_DROPs)
print("PBP shape:", pbp_pl.shape)

# COMMAND ----------

pdf: pd.DataFrame = pbp_pl.to_pandas()
sdf = spark.createDataFrame(pdf)

# COMMAND ----------

def write_delta_from_polars(df_pl: pl.DataFrame, full_table_name: str) -> None:
    """Write a Polars DataFrame to a Delta table via Spark."""
    pdf: pd.DataFrame = df_pl.to_pandas()
    sdf = spark.createDataFrame(pdf)

    (sdf.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_table_name))
    print(f"Wrote table: {full_table_name}  (rows={sdf.count()})")

write_delta_from_polars(pbp_pl, f"{CATALOG}.{SCHEMA}.football_pbp_data")

# COMMAND ----------

display(sdf)

# COMMAND ----------

display(spark.read.table(f"{CATALOG}.{SCHEMA}.football_pbp_data").limit(10))

# COMMAND ----------

