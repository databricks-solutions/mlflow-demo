# Databricks notebook source
# MAGIC %md
# MAGIC #Create the Functions for the Agent to Use
# MAGIC
# MAGIC

# COMMAND ----------

from config.dc_assistant_config import CATALOG, SCHEMA

dbutils.widgets.text("catalog", CATALOG, "Catalog")
dbutils.widgets.text("schema", SCHEMA, "Schema")

# COMMAND ----------

# MAGIC %sql
# MAGIC BEGIN
# MAGIC   FOR r AS
# MAGIC     SELECT routine_name
# MAGIC     FROM ac_demo.information_schema.routines
# MAGIC     WHERE routine_schema = 'dc_assistant'
# MAGIC       AND routine_type = 'FUNCTION'
# MAGIC   DO
# MAGIC     EXECUTE IMMEDIATE
# MAGIC       'DROP FUNCTION IF EXISTS `ac_demo`.`dc_assistant`.`' || r.routine_name || '`';
# MAGIC   END FOR;
# MAGIC END;
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Databricks SQL notebook source
# MAGIC -- Set context (redundant if using three-part names, kept for clarity)
# MAGIC
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC -- Formation tendencies (table function)
# MAGIC CREATE OR REPLACE FUNCTION tendencies_by_offense_formation(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for (e.g., array(2023,2024))',
# MAGIC   redzone BOOLEAN COMMENT 'If TRUE, restrict to red zone plays (yardline_100 <= 20); if NULL/false, include all'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive formation tendencies with parsed personnel buckets'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       offense_formation,
# MAGIC       personnel_bucket,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(pass_plays) AS pass_plays,
# MAGIC       SUM(rush_plays) AS rush_plays,
# MAGIC       SUM(pass_plays) / COUNT(*) AS pass_rate,
# MAGIC       SUM(rush_plays) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(CAST(success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(yards_gained) AS avg_yards
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         a.offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket,
# MAGIC         p.play_type,
# MAGIC         CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END AS pass_plays,
# MAGIC         CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END AS rush_plays,
# MAGIC         p.epa,
# MAGIC         p.success,
# MAGIC         p.yards_gained
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC         AND (redzone IS NULL OR redzone = FALSE OR p.yardline_100 <= 20)
# MAGIC     )
# MAGIC     GROUP BY offense_formation, personnel_bucket
# MAGIC     ORDER BY plays DESC, offense_formation, personnel_bucket
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC -- Down & distance tendencies (offense-only table function)
# MAGIC CREATE OR REPLACE FUNCTION tendencies_by_down_distance(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   redzone BOOLEAN COMMENT 'If TRUE, restrict to red zone plays (yardline_100 <= 20); if NULL/false, include all'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive down & distance tendencies for a team'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'down', down,
# MAGIC         'distance_bucket', distance_bucket,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       down,
# MAGIC       distance_bucket,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(pass_plays) AS pass_plays,
# MAGIC       SUM(rush_plays) AS rush_plays,
# MAGIC       SUM(pass_plays) / COUNT(*) AS pass_rate,
# MAGIC       SUM(rush_plays) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(CAST(success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.down,
# MAGIC         CASE
# MAGIC           WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC           WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC           WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC           ELSE '>10'
# MAGIC         END AS distance_bucket,
# MAGIC         p.play_type,
# MAGIC         CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END AS pass_plays,
# MAGIC         CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END AS rush_plays,
# MAGIC         p.epa,
# MAGIC         p.success,
# MAGIC         p.yards_gained,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch,
# MAGIC         p.first_down
# MAGIC       FROM football_pbp_data p
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND p.down IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC         AND (redzone IS NULL OR redzone = FALSE OR p.yardline_100 <= 20)
# MAGIC     )
# MAGIC     GROUP BY down, distance_bucket
# MAGIC     ORDER BY down, distance_bucket
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC -- Who got the ball given situation (offense-only, filters include formation & personnel bucket)
# MAGIC CREATE OR REPLACE FUNCTION who_got_ball_by_offense_situation(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   offense_formation STRING COMMENT 'Offensive formation to filter by',
# MAGIC   personnel_bucket STRING COMMENT 'Parsed personnel bucket string (e.g., "5 OL, 1 RB, 1 TE, 3 WR, 1 QB")',
# MAGIC   down INT COMMENT 'Down to filter by (1-4)',
# MAGIC   distance_bucket STRING COMMENT 'Distance bucket to filter by: 1-2|3-6|7-10|>10',
# MAGIC   redzone BOOLEAN COMMENT 'If TRUE, restrict to red zone plays (yardline_100 <= 20); if NULL/false, include all'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: who got the ball (receiver on passes, rusher on runs) for a given formation, personnel, down and distance bucket'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'ball_getter', ball_getter,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       ball_getter,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(pass_plays) AS pass_plays,
# MAGIC       SUM(rush_plays) AS rush_plays,
# MAGIC       SUM(pass_plays) / COUNT(*) AS pass_rate,
# MAGIC       SUM(rush_plays) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.play_id,
# MAGIC         p.down,
# MAGIC         CASE
# MAGIC           WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC           WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC           WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC           ELSE '>10'
# MAGIC         END AS distance_bucket_calc,
# MAGIC         a.offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket_calc,
# MAGIC         CASE
# MAGIC           WHEN CAST(p.`pass` AS DOUBLE) = 1 THEN p.receiver
# MAGIC           WHEN CAST(p.rush AS DOUBLE) = 1 THEN p.rusher
# MAGIC           ELSE 'UNKNOWN'
# MAGIC         END AS ball_getter,
# MAGIC         p.posteam,
# MAGIC         p.season,
# MAGIC         p.play_type,
# MAGIC         CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END AS pass_plays,
# MAGIC         CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END AS rush_plays,
# MAGIC         p.epa,
# MAGIC         p.yards_gained,
# MAGIC         p.first_down,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2022, 2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC         AND (redzone IS NULL OR redzone = FALSE OR p.yardline_100 <= 20)
# MAGIC     ) s
# MAGIC     WHERE s.offense_formation = offense_formation
# MAGIC       AND s.personnel_bucket_calc = personnel_bucket
# MAGIC       AND s.down = down
# MAGIC       AND s.distance_bucket_calc = distance_bucket
# MAGIC     GROUP BY ball_getter
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC -- Who got the ball by down & distance and formation (no formation/personnel inputs; grouped by them)
# MAGIC CREATE OR REPLACE FUNCTION who_got_ball_by_down_distance_and_form(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   down INT COMMENT 'Down to filter by (1-4)',
# MAGIC   distance_bucket STRING COMMENT 'Distance bucket to filter by: 1-2|3-6|7-10|>10',
# MAGIC   redzone BOOLEAN COMMENT 'If TRUE, restrict to red zone plays (yardline_100 <= 20); if NULL/false, include all'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: for a down+distance bucket, list who got the ball grouped by offense_formation and personnel bucket'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'ball_getter', ball_getter,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       offense_formation,
# MAGIC       personnel_bucket,
# MAGIC       ball_getter,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(pass_plays) AS pass_plays,
# MAGIC       SUM(rush_plays) AS rush_plays,
# MAGIC       SUM(pass_plays) / COUNT(*) AS pass_rate,
# MAGIC       SUM(rush_plays) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.play_id,
# MAGIC         p.down,
# MAGIC         CASE
# MAGIC           WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC           WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC           WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC           ELSE '>10'
# MAGIC         END AS distance_bucket_calc,
# MAGIC         a.offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket,
# MAGIC         CASE
# MAGIC           WHEN CAST(p.`pass` AS DOUBLE) = 1 THEN p.receiver
# MAGIC           WHEN CAST(p.rush AS DOUBLE) = 1 THEN p.rusher
# MAGIC           ELSE 'UNKNOWN'
# MAGIC         END AS ball_getter,
# MAGIC         p.play_type,
# MAGIC         CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END AS pass_plays,
# MAGIC         CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END AS rush_plays,
# MAGIC         p.epa,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch,
# MAGIC         p.yards_gained,
# MAGIC         p.first_down
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC         AND (redzone IS NULL OR redzone = FALSE OR p.yardline_100 <= 20)
# MAGIC     ) s
# MAGIC     WHERE s.down = down
# MAGIC       AND s.distance_bucket_calc = distance_bucket
# MAGIC     GROUP BY offense_formation, personnel_bucket, ball_getter
# MAGIC     ORDER BY plays DESC, offense_formation, personnel_bucket
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Who got the ball given situation (offense-only table function)
# MAGIC CREATE OR REPLACE FUNCTION who_got_ball_by_offense_situation(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   offense_formation STRING COMMENT 'Offensive formation to filter by',
# MAGIC   personnel_bucket STRING COMMENT 'Parsed personnel bucket string (e.g., "5 OL, 1 RB, 1 TE, 3 WR, 1 QB")',
# MAGIC   down INT COMMENT 'Down to filter by (1-4)',
# MAGIC   distance_bucket STRING COMMENT 'Distance bucket to filter by: 1-2|3-6|7-10|>10'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: who got the ball (receiver on passes, rusher on runs) for a given formation, personnel, down and distance bucket'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'ball_getter', ball_getter,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       ball_getter,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) AS pass_plays,
# MAGIC       SUM(CAST(rush AS DOUBLE)) AS rush_plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CAST(rush AS DOUBLE)) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.play_id,
# MAGIC         p.down,
# MAGIC         CASE
# MAGIC           WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC           WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC           WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC           ELSE '>10'
# MAGIC         END AS distance_bucket_calc,
# MAGIC         a.offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket_calc,
# MAGIC         CASE
# MAGIC           WHEN CAST(p.`pass` AS DOUBLE) = 1 THEN p.receiver
# MAGIC           WHEN CAST(p.rush AS DOUBLE) = 1 THEN p.rusher
# MAGIC           ELSE 'UNKNOWN'
# MAGIC         END AS ball_getter,
# MAGIC         p.posteam,
# MAGIC         p.season,
# MAGIC         p.`pass`,
# MAGIC         p.rush,
# MAGIC         p.epa,
# MAGIC         p.yards_gained,
# MAGIC         p.first_down,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC     ) s
# MAGIC     WHERE s.offense_formation = offense_formation
# MAGIC       AND s.personnel_bucket_calc = personnel_bucket
# MAGIC       AND s.down = down
# MAGIC       AND s.distance_bucket_calc = distance_bucket
# MAGIC     GROUP BY ball_getter
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC
# MAGIC CREATE OR REPLACE FUNCTION who_got_ball_by_down_distance(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   down INT COMMENT 'Down to filter by (1-4)',
# MAGIC   distance_bucket STRING COMMENT 'Distance bucket to filter by: 1-2|3-6|7-10|>10'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: for a down+distance bucket, list who got the ball (receiver on passes, rusher on runs)'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'ball_getter', ball_getter,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       ball_getter,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) AS pass_plays,
# MAGIC       SUM(CAST(rush AS DOUBLE)) AS rush_plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CAST(rush AS DOUBLE)) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.play_id,
# MAGIC         p.down,
# MAGIC         CASE
# MAGIC           WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC           WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC           WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC           ELSE '>10'
# MAGIC         END AS distance_bucket_calc,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket,
# MAGIC         CASE
# MAGIC           WHEN CAST(p.`pass` AS DOUBLE) = 1 THEN p.receiver
# MAGIC           WHEN CAST(p.rush AS DOUBLE) = 1 THEN p.rusher
# MAGIC           ELSE 'UNKNOWN'
# MAGIC         END AS ball_getter,
# MAGIC         p.posteam,
# MAGIC         p.season,
# MAGIC         p.`pass`,
# MAGIC         p.rush,
# MAGIC         p.epa,
# MAGIC         p.yards_gained,
# MAGIC         p.first_down,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC     ) s
# MAGIC     WHERE s.down = down
# MAGIC       AND s.distance_bucket_calc = distance_bucket
# MAGIC     GROUP BY ball_getter
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC
# MAGIC CREATE OR REPLACE FUNCTION pbp_star()
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: sample of football_pbp_data (first 100 rows) for agent/cursor context'
# MAGIC RETURN (
# MAGIC   SELECT to_json(collect_list(struct(*)))
# MAGIC   FROM (
# MAGIC     SELECT *
# MAGIC     FROM football_pbp_data
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC
# MAGIC
# MAGIC CREATE OR REPLACE FUNCTION participation_star()
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: sample of football_participation (first 100 rows) for agent/cursor context'
# MAGIC RETURN (
# MAGIC   SELECT to_json(collect_list(struct(*)))
# MAGIC   FROM (
# MAGIC     SELECT *
# MAGIC     FROM football_participation
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- First play after turnover tendencies
# MAGIC CREATE OR REPLACE FUNCTION first_play_after_turnover(
# MAGIC   team STRING COMMENT 'Team abbrev used in pbp posteam (ex: SF, KC)',
# MAGIC   seasons ARRAY<INT> COMMENT 'Seasons to include (ex: array(2023,2024))'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive play tendencies for first play after turnover'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'play_type', play_type,
# MAGIC         'plays', plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     -- your existing SELECT ... GROUP BY ...
# MAGIC     SELECT
# MAGIC       a.offense_formation,
# MAGIC       CONCAT(/* ... your personnel_bucket logic ... */) AS personnel_bucket,
# MAGIC       p.play_type,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(CAST(success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(yards_gained) AS avg_yards
# MAGIC     FROM football_pbp_data p
# MAGIC     LEFT JOIN football_participation a
# MAGIC       ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id) AND p.play_id = a.play_id
# MAGIC     WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC       AND p.posteam = team
# MAGIC       AND p.play_id = p.drive_play_id_started
# MAGIC       AND p.drive_end_transition IN ('INTERCEPTION', 'FUMBLE')
# MAGIC       AND a.offense_formation IS NOT NULL
# MAGIC       AND a.offense_personnel IS NOT NULL
# MAGIC       AND p.play_type IN ('pass', 'run')
# MAGIC     GROUP BY a.offense_formation, personnel_bucket, p.play_type
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 50
# MAGIC   )
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Tendencies by score in 2nd half
# MAGIC CREATE OR REPLACE FUNCTION tendencies_by_score_2nd_half(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive tendencies by score differential in 2nd half (Winning >10, Winning 1-9, Tied, Losing 1-9, Losing >10)'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'score_situation', score_situation,
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       score_situation,
# MAGIC       offense_formation,
# MAGIC       personnel_bucket,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CASE WHEN play_type = 'pass' THEN 1 ELSE 0 END) AS pass_plays,
# MAGIC       SUM(CASE WHEN play_type = 'run'  THEN 1 ELSE 0 END) AS rush_plays,
# MAGIC       SUM(CASE WHEN play_type = 'pass' THEN 1 ELSE 0 END) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CASE WHEN play_type = 'run'  THEN 1 ELSE 0 END) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(CAST(success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(yards_gained) AS avg_yards
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         CASE
# MAGIC           WHEN p.score_differential > 10 THEN 'Winning >10'
# MAGIC           WHEN p.score_differential BETWEEN 1 AND 9 THEN 'Winning 1-9'
# MAGIC           WHEN p.score_differential = 0 THEN 'Tied'
# MAGIC           WHEN p.score_differential BETWEEN -9 AND -1 THEN 'Losing 1-9'
# MAGIC           WHEN p.score_differential < -10 THEN 'Losing >10'
# MAGIC         END AS score_situation,
# MAGIC         a.offense_formation AS offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket,
# MAGIC         p.play_type,
# MAGIC         p.epa,
# MAGIC         p.success,
# MAGIC         p.yards_gained
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND p.game_half = 'Half2'
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC     ) s
# MAGIC     GROUP BY score_situation, offense_formation, personnel_bucket
# MAGIC     ORDER BY score_situation, plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Tendencies by drive start position
# MAGIC CREATE OR REPLACE FUNCTION tendencies_by_drive_start(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive tendencies by drive start position (own <25, own 25-50, opponent territory)'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'drive_start_zone', drive_start_zone,
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       drive_start_zone,
# MAGIC       offense_formation,
# MAGIC       personnel_bucket,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CASE WHEN play_type = 'pass' THEN 1 ELSE 0 END) AS pass_plays,
# MAGIC       SUM(CASE WHEN play_type = 'run'  THEN 1 ELSE 0 END) AS rush_plays,
# MAGIC       SUM(CASE WHEN play_type = 'pass' THEN 1 ELSE 0 END) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CASE WHEN play_type = 'run'  THEN 1 ELSE 0 END) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(CAST(success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(yards_gained) AS avg_yards
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         CASE
# MAGIC           WHEN p.yardline_100 > 75 THEN 'Own <25'
# MAGIC           WHEN p.yardline_100 BETWEEN 50 AND 75 THEN 'Own 25-50'
# MAGIC           WHEN p.yardline_100 < 50 THEN 'Opponent Territory'
# MAGIC         END AS drive_start_zone,
# MAGIC         a.offense_formation AS offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket,
# MAGIC         p.play_type,
# MAGIC         p.epa,
# MAGIC         p.success,
# MAGIC         p.yards_gained
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND p.play_id = p.drive_play_id_started
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND p.play_type IN ('pass', 'run')
# MAGIC     ) s
# MAGIC     GROUP BY drive_start_zone, offense_formation, personnel_bucket
# MAGIC     ORDER BY drive_start_zone, plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Two-minute drill tendencies (update to existing formations function)
# MAGIC CREATE OR REPLACE FUNCTION tendencies_two_minute_drill(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   two_minute_drill BOOLEAN COMMENT 'If TRUE, restrict to plays with <2 minutes in 2nd or 4th quarter'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive formation tendencies during two-minute drill situations (under 2 minutes in 2nd or 4th quarter)'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       a.offense_formation AS offense_formation,
# MAGIC       CONCAT(
# MAGIC         CAST(GREATEST(
# MAGIC           0,
# MAGIC           10 - (
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC           )
# MAGIC         ) AS STRING), ' OL, ',
# MAGIC         CAST(
# MAGIC           COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC           + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC         AS STRING), ' RB, ',
# MAGIC         CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC         CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC       ) AS personnel_bucket,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END) AS pass_plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END) AS rush_plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END) / COUNT(*) AS rush_rate,
# MAGIC       AVG(p.epa) AS avg_epa,
# MAGIC       AVG(CAST(p.success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(p.yards_gained) AS avg_yards,
# MAGIC       AVG(p.air_yards) AS avg_air_yards,
# MAGIC       AVG(p.yards_after_catch) AS avg_yards_after_catch
# MAGIC     FROM football_pbp_data p
# MAGIC     LEFT JOIN football_participation a
# MAGIC       ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC      AND p.play_id = a.play_id
# MAGIC     WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC       AND p.posteam = team
# MAGIC       AND a.offense_formation IS NOT NULL
# MAGIC       AND a.offense_personnel IS NOT NULL
# MAGIC       AND p.play_type IN ('pass', 'run')
# MAGIC       AND (
# MAGIC         two_minute_drill IS NULL
# MAGIC         OR two_minute_drill = FALSE
# MAGIC         OR (
# MAGIC           two_minute_drill = TRUE
# MAGIC           AND (
# MAGIC             (p.qtr = 2 AND p.quarter_seconds_remaining <= 120)
# MAGIC             OR (p.qtr = 4 AND p.quarter_seconds_remaining <= 120)
# MAGIC           )
# MAGIC         )
# MAGIC       )
# MAGIC     GROUP BY a.offense_formation, personnel_bucket
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Who gets the ball during two-minute drill
# MAGIC CREATE OR REPLACE FUNCTION who_got_ball_two_minute_drill(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for',
# MAGIC   offense_formation STRING COMMENT 'Offensive formation to filter by',
# MAGIC   personnel_bucket STRING COMMENT 'Parsed personnel bucket string (e.g., \"5 OL, 1 RB, 1 TE, 3 WR, 1 QB\")',
# MAGIC   two_minute_drill BOOLEAN COMMENT 'If TRUE, restrict to plays with <2 minutes in 2nd or 4th quarter'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: who got the ball during two-minute drill situations (receiver on passes, rusher on runs) for a given formation/personnel'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'ball_getter', ball_getter,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       ball_getter,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) AS pass_plays,
# MAGIC       SUM(CAST(rush AS DOUBLE)) AS rush_plays,
# MAGIC       SUM(CAST(`pass` AS DOUBLE)) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CAST(rush AS DOUBLE)) / COUNT(*) AS rush_rate,
# MAGIC       AVG(epa) AS avg_epa,
# MAGIC       AVG(yards_gained) AS avg_yards,
# MAGIC       AVG(air_yards) AS avg_air_yards,
# MAGIC       AVG(yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(first_down) AS first_down_rate
# MAGIC     FROM (
# MAGIC       SELECT
# MAGIC         p.play_id,
# MAGIC         a.offense_formation,
# MAGIC         CONCAT(
# MAGIC           CAST(GREATEST(
# MAGIC             0,
# MAGIC             10 - (
# MAGIC               COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC               + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC             )
# MAGIC           ) AS STRING), ' OL, ',
# MAGIC           CAST(
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC           AS STRING), ' RB, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC           CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC         ) AS personnel_bucket_calc,
# MAGIC         CASE
# MAGIC           WHEN CAST(p.`pass` AS DOUBLE) = 1 THEN p.receiver
# MAGIC           WHEN CAST(p.rush AS DOUBLE) = 1 THEN p.rusher
# MAGIC           ELSE 'UNKNOWN'
# MAGIC         END AS ball_getter,
# MAGIC         p.posteam,
# MAGIC         p.season,
# MAGIC         p.`pass`,
# MAGIC         p.rush,
# MAGIC         p.epa,
# MAGIC         p.yards_gained,
# MAGIC         p.first_down,
# MAGIC         p.air_yards,
# MAGIC         p.yards_after_catch
# MAGIC       FROM football_pbp_data p
# MAGIC       LEFT JOIN football_participation a
# MAGIC         ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC        AND p.play_id = a.play_id
# MAGIC       WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC         AND p.posteam = team
# MAGIC         AND a.offense_formation IS NOT NULL
# MAGIC         AND a.offense_personnel IS NOT NULL
# MAGIC         AND (
# MAGIC           two_minute_drill IS NULL
# MAGIC           OR two_minute_drill = FALSE
# MAGIC           OR (
# MAGIC             two_minute_drill = TRUE
# MAGIC             AND (
# MAGIC               (p.qtr = 2 AND p.quarter_seconds_remaining <= 120)
# MAGIC               OR (p.qtr = 4 AND p.quarter_seconds_remaining <= 120)
# MAGIC             )
# MAGIC           )
# MAGIC         )
# MAGIC     ) s
# MAGIC     WHERE s.offense_formation = offense_formation
# MAGIC       AND s.personnel_bucket_calc = personnel_bucket
# MAGIC     GROUP BY ball_getter
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Offensive success rate by pass rushers and defensive coverage
# MAGIC CREATE OR REPLACE FUNCTION success_by_pass_rush_and_coverage(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: offensive success by number of pass rushers, man/zone type, and coverage type'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'number_of_pass_rushers', number_of_pass_rushers,
# MAGIC         'defense_man_zone_type', defense_man_zone_type,
# MAGIC         'defense_coverage_type', defense_coverage_type,
# MAGIC         'plays', plays,
# MAGIC         'pass_plays', pass_plays,
# MAGIC         'rush_plays', rush_plays,
# MAGIC         'pass_rate', pass_rate,
# MAGIC         'rush_rate', rush_rate,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_air_yards', avg_air_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       a.number_of_pass_rushers AS number_of_pass_rushers,
# MAGIC       a.defense_man_zone_type AS defense_man_zone_type,
# MAGIC       a.defense_coverage_type AS defense_coverage_type,
# MAGIC       COUNT(*) AS plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END) AS pass_plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END) AS rush_plays,
# MAGIC       SUM(CASE WHEN p.play_type = 'pass' THEN 1 ELSE 0 END) / COUNT(*) AS pass_rate,
# MAGIC       SUM(CASE WHEN p.play_type = 'run'  THEN 1 ELSE 0 END) / COUNT(*) AS rush_rate,
# MAGIC       AVG(p.epa) AS avg_epa,
# MAGIC       AVG(CAST(p.success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(p.yards_gained) AS avg_yards,
# MAGIC       AVG(p.air_yards) AS avg_air_yards,
# MAGIC       AVG(p.yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(p.first_down) AS first_down_rate
# MAGIC     FROM football_pbp_data p
# MAGIC     INNER JOIN football_participation a
# MAGIC       ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC      AND p.play_id = a.play_id
# MAGIC     WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC       AND p.posteam = team
# MAGIC       AND a.number_of_pass_rushers IS NOT NULL
# MAGIC       AND a.defense_man_zone_type IS NOT NULL
# MAGIC       AND a.defense_coverage_type IS NOT NULL
# MAGIC       AND p.play_type IN ('pass', 'run')
# MAGIC     GROUP BY a.number_of_pass_rushers, a.defense_man_zone_type, a.defense_coverage_type
# MAGIC     ORDER BY plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog);
# MAGIC USE SCHEMA IDENTIFIER(:schema);
# MAGIC -- COMMAND ----------
# MAGIC -- Screen play tendencies by down and distance
# MAGIC CREATE OR REPLACE FUNCTION screen_play_tendencies(
# MAGIC   team STRING COMMENT 'The team to collect tendencies for',
# MAGIC   seasons ARRAY<INT> COMMENT 'The seasons to collect tendencies for'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'JSON rows: screen play tendencies (route=SCREEN) by down, distance, formation, personnel, and primary receiver'
# MAGIC RETURN (
# MAGIC   SELECT to_json(
# MAGIC     collect_list(
# MAGIC       named_struct(
# MAGIC         'down', down,
# MAGIC         'distance_bucket', distance_bucket,
# MAGIC         'offense_formation', offense_formation,
# MAGIC         'personnel_bucket', personnel_bucket,
# MAGIC         'primary_receiver', primary_receiver,
# MAGIC         'plays', plays,
# MAGIC         'avg_epa', avg_epa,
# MAGIC         'success_rate', success_rate,
# MAGIC         'avg_yards', avg_yards,
# MAGIC         'avg_yards_after_catch', avg_yards_after_catch,
# MAGIC         'first_down_rate', first_down_rate
# MAGIC       )
# MAGIC     )
# MAGIC   )
# MAGIC   FROM (
# MAGIC     SELECT
# MAGIC       p.down AS down,
# MAGIC       CASE
# MAGIC         WHEN p.ydstogo <= 2 THEN '1-2'
# MAGIC         WHEN p.ydstogo <= 6 THEN '3-6'
# MAGIC         WHEN p.ydstogo <= 10 THEN '7-10'
# MAGIC         ELSE '>10'
# MAGIC       END AS distance_bucket,
# MAGIC       a.offense_formation AS offense_formation,
# MAGIC       CONCAT(
# MAGIC         CAST(GREATEST(
# MAGIC           0,
# MAGIC           10 - (
# MAGIC             COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0)
# MAGIC             + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0)
# MAGIC           )
# MAGIC         ) AS STRING), ' OL, ',
# MAGIC         CAST(
# MAGIC           COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*RB', 1) AS INT), 0)
# MAGIC           + COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*FB', 1) AS INT), 0)
# MAGIC         AS STRING), ' RB, ',
# MAGIC         CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*TE', 1) AS INT), 0) AS STRING), ' TE, ',
# MAGIC         CAST(COALESCE(TRY_CAST(REGEXP_EXTRACT(a.offense_personnel, '(?i)(\\d+)\\s*WR', 1) AS INT), 0) AS STRING), ' WR, 1 QB'
# MAGIC       ) AS personnel_bucket,
# MAGIC       COALESCE(CAST(p.receiver AS STRING), 'UNKNOWN') AS primary_receiver,
# MAGIC       COUNT(*) AS plays,
# MAGIC       AVG(p.epa) AS avg_epa,
# MAGIC       AVG(CAST(p.success AS DOUBLE)) AS success_rate,
# MAGIC       AVG(p.yards_gained) AS avg_yards,
# MAGIC       AVG(p.yards_after_catch) AS avg_yards_after_catch,
# MAGIC       AVG(p.first_down) AS first_down_rate
# MAGIC     FROM football_pbp_data p
# MAGIC     INNER JOIN football_participation a
# MAGIC       ON p.game_id = COALESCE(a.nflverse_game_id, a.old_game_id)
# MAGIC      AND p.play_id = a.play_id
# MAGIC     WHERE array_contains(COALESCE(seasons, array(2023, 2024)), p.season)
# MAGIC       AND p.posteam = team
# MAGIC       AND a.route = 'SCREEN'
# MAGIC       AND a.offense_formation IS NOT NULL
# MAGIC       AND a.offense_personnel IS NOT NULL
# MAGIC       AND p.down IS NOT NULL
# MAGIC     GROUP BY
# MAGIC       p.down,
# MAGIC       distance_bucket,
# MAGIC       a.offense_formation,
# MAGIC       personnel_bucket,
# MAGIC       primary_receiver
# MAGIC     ORDER BY p.down, distance_bucket, plays DESC
# MAGIC     LIMIT 100
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC

# COMMAND ----------

