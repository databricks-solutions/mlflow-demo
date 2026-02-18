# Auto-generated configuration file
# Do not edit manually - regenerate from 00_setup.ipynb

CATALOG = "ac_demo"
SCHEMA = "dc_assistant"
SEASONS = [2022, 2023, 2024]
EXPERIMENT_ID = "2517718719552044"
PROMPT_NAME = "ac_demo.dc_assistant.dcassistant"
# LLM_ENDPOINT_NAME = "databricks-gpt-5-mini"
LLM_ENDPOINT_NAME = "databricks-gpt-5-2"
# LLM_ENDPOINT_NAME = "databricks-gemini-3-flash"
JUDGE_MODEL = "databricks:/databricks-gpt-5-2"
MODEL_NAME = "ac_dc_assistant"
UC_MODEL_NAME = "ac_demo.dc_assistant.ac_dc_assistant"
DATASET_NAME = "ac_demo.dc_assistant.dc_assistant_eval_trace_data"
LABELING_SESSION_NAME = "dcassistant_eval_labeling"
ASSIGNED_USERS = ['austin.choi@databricks.com']
ALIGNED_JUDGE_NAME = "football_analysis_judge_align"
UC_TOOL_NAMES = ['ac_demo.dc_assistant.who_got_ball_by_down_distance', 'ac_demo.dc_assistant.who_got_ball_by_offense_situation', 'ac_demo.dc_assistant.tendencies_by_offense_formation', 'ac_demo.dc_assistant.tendencies_by_down_distance', 'ac_demo.dc_assistant.tendencies_by_drive_start', 'ac_demo.dc_assistant.tendencies_by_score_2nd_half', 'ac_demo.dc_assistant.tendencies_two_minute_drill', 'ac_demo.dc_assistant.who_got_ball_by_down_distance_and_form', 'ac_demo.dc_assistant.who_got_ball_two_minute_drill', 'ac_demo.dc_assistant.first_play_after_turnover', 'ac_demo.dc_assistant.screen_play_tendencies', 'ac_demo.dc_assistant.success_by_pass_rush_and_coverage']
USE_OAUTH = True
SECRET_SCOPE_NAME = "dc-assistant-secrets"
OAUTH_CLIENT_ID_KEY = "oauth-client-id"
OAUTH_CLIENT_SECRET_KEY = "oauth-client-secret"
PAT_KEY = "databricks-pat"
DATABRICKS_HOST = "https://e2-demo-field-eng.cloud.databricks.com/"
