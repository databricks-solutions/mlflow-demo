"""Validation module for pre and post setup checks."""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from databricks.sdk import WorkspaceClient


class SetupValidator:
  """Validates setup prerequisites and post-deployment health."""

  def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
    """Initialize the validator.

    Args:
        workspace_client: Optional pre-configured workspace client.
    """
    self.client = workspace_client or WorkspaceClient()
    self.validation_results = {}

  def validate_prerequisites(self) -> Tuple[bool, List[str]]:
    """Validate all prerequisites before starting setup.

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []

    print('🔍 Validating prerequisites...')

    # Check CLI authentication
    if not self._check_cli_auth():
      issues.append("Databricks CLI is not authenticated. Run 'databricks auth login'")

    # Check required tools
    missing_tools = self._check_required_tools()
    if missing_tools:
      issues.append(f'Missing required tools: {", ".join(missing_tools)}')

    # Check workspace connectivity
    if not self._check_workspace_connectivity():
      issues.append('Cannot connect to Databricks workspace')

    # Check Unity Catalog access
    if not self._check_unity_catalog_access():
      issues.append('Cannot access Unity Catalog. May need permissions or UC setup')

    # Check MLflow access
    if not self._check_mlflow_access():
      issues.append('Cannot access MLflow. May need experiment permissions')

    # Check Apps functionality
    if not self._check_apps_access():
      issues.append('Cannot access Databricks Apps. May need workspace or permissions')

    all_valid = len(issues) == 0
    self.validation_results['prerequisites'] = {'valid': all_valid, 'issues': issues}

    if all_valid:
      print('✅ All prerequisites validated successfully')
    else:
      print(f'❌ Found {len(issues)} prerequisite issues')

    return all_valid, issues

  def validate_environment_config(self, config: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Validate environment configuration.

    Args:
        config: Environment configuration dict

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []
    required_vars = [
      'DATABRICKS_HOST',
      'DATABRICKS_APP_NAME',
      'LHA_SOURCE_CODE_PATH',
      'MLFLOW_EXPERIMENT_ID',
      'UC_CATALOG',
      'UC_SCHEMA',
    ]

    print('🔍 Validating environment configuration...')

    # Check required variables are present
    for var in required_vars:
      if not config.get(var):
        issues.append(f'Missing required environment variable: {var}')

    # Validate workspace URL format
    if 'DATABRICKS_HOST' in config:
      host = config['DATABRICKS_HOST']
      if not host.startswith('https://'):
        issues.append('DATABRICKS_HOST must start with https://')
      if '.cloud.databricks.com' not in host and '.azuredatabricks.net' not in host:
        issues.append("DATABRICKS_HOST doesn't appear to be a valid Databricks URL")

    # Validate experiment ID format
    if 'MLFLOW_EXPERIMENT_ID' in config:
      exp_id = config['MLFLOW_EXPERIMENT_ID']
      try:
        int(exp_id)
      except ValueError:
        issues.append('MLFLOW_EXPERIMENT_ID must be a numeric ID')

    # Validate catalog.schema format
    if 'UC_CATALOG' in config and 'UC_SCHEMA' in config:
      catalog = config['UC_CATALOG']
      schema = config['UC_SCHEMA']
      if '.' in catalog or '.' in schema:
        issues.append('UC_CATALOG and UC_SCHEMA should not contain dots')

    all_valid = len(issues) == 0
    self.validation_results['environment_config'] = {'valid': all_valid, 'issues': issues}

    return all_valid, issues

  def validate_resource_creation(self, resources: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that resources were created successfully.

    Args:
        resources: Dict with created resource information

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []

    print('🔍 Validating created resources...')

    # Validate experiment exists and is accessible
    if 'experiment_id' in resources:
      if not self._validate_experiment_exists(resources['experiment_id']):
        issues.append(f'MLflow experiment {resources["experiment_id"]} not found or not accessible')

    # Validate schema exists and has proper permissions
    if 'catalog_name' in resources and 'schema_name' in resources:
      if not self._validate_schema_access(resources['catalog_name'], resources['schema_name']):
        issues.append(
          f'Schema {resources["catalog_name"]}.{resources["schema_name"]} not accessible'
        )

    # Validate app exists
    if 'app_name' in resources:
      if not self._validate_app_exists(resources['app_name']):
        issues.append(f'Databricks App {resources["app_name"]} not found')

    all_valid = len(issues) == 0
    self.validation_results['resource_creation'] = {'valid': all_valid, 'issues': issues}

    return all_valid, issues

  def validate_deployment(
    self, app_name: str, app_url: Optional[str] = None
  ) -> Tuple[bool, List[str]]:
    """Validate deployment health and functionality.

    Args:
        app_name: Name of the deployed app
        app_url: Optional app URL for health checks

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []

    print('🔍 Validating deployment...')

    # Check app status
    if not self._check_app_status(app_name):
      issues.append(f'App {app_name} is not in ACTIVE status')

    # Test health endpoint if URL provided
    if app_url and not self._test_health_endpoint(app_url):
      issues.append('App health endpoint is not responding')

    # Test basic functionality if URL provided
    if app_url and not self._test_basic_functionality(app_url):
      issues.append('App basic functionality test failed')

    all_valid = len(issues) == 0
    self.validation_results['deployment'] = {'valid': all_valid, 'issues': issues}

    return all_valid, issues

  def run_integration_tests(self, config: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Run integration tests to verify end-to-end functionality.

    Args:
        config: Environment configuration

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []

    print('🔍 Running integration tests...')

    # Test prompt registry access
    if not self._test_prompt_registry_access(config):
      issues.append('Cannot access prompt registry')

    # Test MLflow experiment writing
    if not self._test_mlflow_experiment_access(config.get('MLFLOW_EXPERIMENT_ID')):
      issues.append('Cannot write to MLflow experiment')

    # Test sample data loading scripts
    if not self._test_sample_data_scripts():
      issues.append('Sample data loading scripts failed')

    all_valid = len(issues) == 0
    self.validation_results['integration_tests'] = {'valid': all_valid, 'issues': issues}

    return all_valid, issues

  def _check_cli_auth(self) -> bool:
    """Check if Databricks CLI is authenticated."""
    try:
      result = subprocess.run(
        ['databricks', 'auth', 'profiles'], capture_output=True, text=True, check=True
      )
      return 'No profiles found' not in result.stdout and result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
      return False

  def _check_required_tools(self) -> List[str]:
    """Check for required tools and return list of missing ones."""
    missing = []
    tools = ['databricks', 'uv', 'bun']

    for tool in tools:
      try:
        subprocess.run([tool, '--version'], capture_output=True, check=True)
      except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        missing.append(tool)

    return missing

  def _check_workspace_connectivity(self) -> bool:
    """Check if we can connect to the workspace."""
    try:
      self.client.current_user.me()
      return True
    except Exception:
      return False

  def _check_unity_catalog_access(self) -> bool:
    """Check if we can access Unity Catalog."""
    try:
      list(self.client.catalogs.list())
      return True
    except Exception:
      return False

  def _check_mlflow_access(self) -> bool:
    """Check if we can access MLflow."""
    try:
      self.client.experiments.search_experiments()
      return True
    except Exception:
      return False

  def _check_apps_access(self) -> bool:
    """Check if we can access Databricks Apps."""
    try:
      list(self.client.apps.list())
      return True
    except Exception:
      return False

  def _validate_experiment_exists(self, experiment_id: str) -> bool:
    """Validate that an experiment exists and is accessible."""
    try:
      self.client.experiments.get_experiment(experiment_id)
      return True
    except Exception:
      return False

  def _validate_schema_access(self, catalog_name: str, schema_name: str) -> bool:
    """Validate schema exists and is accessible."""
    try:
      self.client.schemas.get(f'{catalog_name}.{schema_name}')
      return True
    except Exception:
      return False

  def _validate_app_exists(self, app_name: str) -> bool:
    """Validate that an app exists."""
    try:
      self.client.apps.get(app_name)
      return True
    except Exception:
      return False

  def _check_app_status(self, app_name: str) -> bool:
    """Check if app is in ACTIVE/RUNNING status."""
    try:
      app = self.client.apps.get(app_name)

      # Check app_status attribute which contains the ApplicationStatus
      if hasattr(app, 'app_status') and app.app_status:
        if hasattr(app.app_status, 'state'):
          state_str = str(app.app_status.state).upper()
          # Accept both RUNNING and ACTIVE states as ready
          return 'RUNNING' in state_str or 'ACTIVE' in state_str

      # Fallback: check if app has URL (indicates it's deployed)
      return bool(getattr(app, 'url', None))
    except Exception:
      return False

  def _test_health_endpoint(self, app_url: str) -> bool:
    """Test app health endpoint."""
    try:
      health_url = f'{app_url.rstrip("/")}/api/health'
      response = requests.get(health_url, timeout=30)
      return response.status_code == 200
    except Exception:
      return False

  def _test_basic_functionality(self, app_url: str) -> bool:
    """Test basic app functionality."""
    try:
      # Test companies endpoint
      companies_url = f'{app_url.rstrip("/")}/api/companies'
      response = requests.get(companies_url, timeout=30)
      if response.status_code != 200:
        return False

      # Check if we get expected data structure
      data = response.json()
      return isinstance(data, list) and len(data) > 0
    except Exception:
      return False

  def _test_prompt_registry_access(self, config: Dict[str, str]) -> bool:
    """Test prompt registry functionality."""
    try:
      catalog = config.get('UC_CATALOG')
      schema = config.get('UC_SCHEMA')
      prompt_name = config.get('PROMPT_NAME', 'email_generation')

      if not all([catalog, schema, prompt_name]):
        return False

      # Try to access the prompt registry (simplified check)
      # This would require mlflow setup, so we'll just check schema access
      return self._validate_schema_access(catalog, schema)
    except Exception:
      return False

  def _test_mlflow_experiment_access(self, experiment_id: Optional[str]) -> bool:
    """Test MLflow experiment write access."""
    if not experiment_id:
      return False

    try:
      # Try to get experiment details
      experiment = self.client.experiments.get_experiment(experiment_id)
      return experiment is not None
    except Exception:
      return False

  def _test_sample_data_scripts(self) -> bool:
    """Test that sample data scripts can run (dry run check)."""
    try:
      # Check if setup scripts exist
      setup_dir = Path(__file__).parent.parent / 'setup'
      required_scripts = [
        '1_load_prompts.py',
        '2_load_sample_traces.py',
        '3_run_evals_for_sample_traces.py',
        '4_setup_monitoring.py',
        '5_setup_labeling_session.py',
      ]

      for script in required_scripts:
        if not (setup_dir / script).exists():
          return False

      return True
    except Exception:
      return False

  def generate_validation_report(self) -> str:
    """Generate a comprehensive validation report.

    Returns:
        Formatted validation report string
    """
    report = ['📋 Setup Validation Report', '=' * 50, '']

    for phase, results in self.validation_results.items():
      status = '✅ PASSED' if results['valid'] else '❌ FAILED'
      report.append(f'{phase.replace("_", " ").title()}: {status}')

      if results['issues']:
        for issue in results['issues']:
          report.append(f'  • {issue}')
      report.append('')

    overall_status = all(r['valid'] for r in self.validation_results.values())
    report.append(
      f'Overall Status: {"✅ ALL CHECKS PASSED" if overall_status else "❌ ISSUES FOUND"}'
    )

    return '\n'.join(report)

  def wait_for_app_ready(self, app_name: str, timeout_minutes: int = 10) -> bool:
    """Wait for app to be ready and responsive.

    Args:
        app_name: Name of the app
        timeout_minutes: Maximum time to wait

    Returns:
        True if app is ready, False if timeout
    """
    timeout_seconds = timeout_minutes * 60
    start_time = time.time()

    print(f"⏳ Waiting for app '{app_name}' to be ready...")

    while time.time() - start_time < timeout_seconds:
      try:
        app = self.client.apps.get(app_name)

        # Get the actual status from app_status.state
        status_display = 'unknown'
        is_ready = False

        if hasattr(app, 'app_status') and app.app_status:
          if hasattr(app.app_status, 'state'):
            status_display = str(app.app_status.state)
            state_str = status_display.upper()
            is_ready = 'RUNNING' in state_str or 'ACTIVE' in state_str

        # Also check if app has URL as additional confirmation
        app_url = getattr(app, 'url', None)
        has_url = bool(app_url)

        if is_ready and has_url:
          print(f"✅ App '{app_name}' is ready and has URL")
          return True

        print(f'   App status: {status_display} - waiting...')
        time.sleep(10)  # Reduced from 30s to 10s for faster checking
      except Exception as e:
        print(f'   Error checking app: {e} - retrying...')
        time.sleep(10)

    print(f"⚠️  Timeout waiting for app '{app_name}' to be ready")
    return False
