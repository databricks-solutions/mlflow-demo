"""Progress tracker for monitoring and resuming setup operations."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class StepStatus(Enum):
  """Status of a setup step."""

  PENDING = 'pending'
  IN_PROGRESS = 'in_progress'
  COMPLETED = 'completed'
  FAILED = 'failed'
  SKIPPED = 'skipped'


@dataclass
class SetupStep:
  """Represents a setup step with metadata."""

  id: str
  name: str
  description: str
  status: StepStatus = StepStatus.PENDING
  start_time: Optional[str] = None
  end_time: Optional[str] = None
  duration_seconds: Optional[float] = None
  error_message: Optional[str] = None
  result_data: Optional[Dict[str, Any]] = None
  dependencies: List[str] = None

  def __post_init__(self):
    if self.dependencies is None:
      self.dependencies = []


class ProgressTracker:
  """Tracks setup progress and enables resume functionality."""

  def __init__(self, project_root: Optional[Path] = None):
    """Initialize the progress tracker.

    Args:
        project_root: Root directory of the project. If None, auto-detects.
    """
    self.project_root = project_root or Path(__file__).parent.parent
    self.progress_file = self.project_root / '.setup_progress.json'
    self.steps: Dict[str, SetupStep] = {}
    self.current_step: Optional[str] = None
    self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Define the complete setup workflow
    self._initialize_steps()

    # Load existing progress if available
    self._load_progress()

  def _initialize_steps(self):
    """Initialize the complete setup workflow steps."""
    step_definitions = [
      {
        'id': 'validate_prerequisites',
        'name': 'Validate Prerequisites',
        'description': 'Check CLI auth, tools, and workspace connectivity',
        'dependencies': [],
      },
      {
        'id': 'detect_environment',
        'name': 'Detect Environment',
        'description': 'Auto-discover workspace settings and suggest configurations',
        'dependencies': ['validate_prerequisites'],
      },
      {
        'id': 'collect_user_input',
        'name': 'Collect User Input',
        'description': 'Gather required configuration from user',
        'dependencies': ['detect_environment'],
      },
      {
        'id': 'validate_config',
        'name': 'Validate Configuration',
        'description': 'Validate environment configuration',
        'dependencies': ['collect_user_input'],
      },
      {
        'id': 'show_installation_preview',
        'name': 'Installation Preview',
        'description': 'Show what will be created and get user confirmation',
        'dependencies': ['validate_config'],
      },
      {
        'id': 'create_catalog_schema',
        'name': 'Create Catalog & Schema',
        'description': 'Create Unity Catalog resources if needed',
        'dependencies': ['show_installation_preview'],
      },
      {
        'id': 'create_experiment',
        'name': 'Create MLflow Experiment',
        'description': 'Create MLflow experiment for tracking',
        'dependencies': ['create_catalog_schema'],
      },
      {
        'id': 'create_app',
        'name': 'Create Databricks App',
        'description': 'Create Databricks App resource',
        'dependencies': ['create_experiment'],
      },
      {
        'id': 'generate_env_file',
        'name': 'Generate Environment File',
        'description': 'Create .env.local with all configuration',
        'dependencies': ['create_app'],
      },
      {
        'id': 'install_dependencies',
        'name': 'Install Dependencies',
        'description': 'Install Python and frontend dependencies',
        'dependencies': ['generate_env_file'],
      },
      {
        'id': 'load_sample_data',
        'name': 'Load Sample Data',
        'description': 'Run setup scripts to load prompts, traces, and evaluations',
        'dependencies': ['install_dependencies'],
      },
      {
        'id': 'validate_local_setup',
        'name': 'Validate Local Setup',
        'description': 'Test local development server functionality',
        'dependencies': ['load_sample_data'],
      },
      {
        'id': 'setup_permissions',
        'name': 'Setup Permissions',
        'description': 'Configure permissions for app service principal',
        'dependencies': ['create_app'],
      },
      {
        'id': 'deploy_app',
        'name': 'Deploy Application',
        'description': 'Build and deploy app to Databricks',
        'dependencies': ['validate_local_setup', 'setup_permissions'],
      },
      {
        'id': 'validate_deployment',
        'name': 'Validate Deployment',
        'description': 'Test deployed app functionality',
        'dependencies': ['setup_permissions'],
      },
      {
        'id': 'run_integration_tests',
        'name': 'Integration Tests',
        'description': 'Run end-to-end integration tests',
        'dependencies': ['validate_deployment'],
      },
    ]

    for step_def in step_definitions:
      step = SetupStep(**step_def)
      self.steps[step.id] = step

  def _load_progress(self):
    """Load existing progress from file."""
    if self.progress_file.exists():
      try:
        with open(self.progress_file, 'r') as f:
          data = json.load(f)

        # Restore steps from saved data
        if 'steps' in data:
          for step_id, step_data in data['steps'].items():
            if step_id in self.steps:
              # Update existing step with saved data
              for key, value in step_data.items():
                if key == 'status':
                  setattr(self.steps[step_id], key, StepStatus(value))
                else:
                  setattr(self.steps[step_id], key, value)

        print(f'📁 Loaded existing progress from {self.progress_file}')
        self._show_progress_summary()
      except Exception as e:
        print(f'⚠️  Could not load existing progress: {e}')

  def _save_progress(self):
    """Save current progress to file."""
    try:
      # Convert steps to serializable format
      data = {
        'session_id': self.session_id,
        'last_updated': datetime.now().isoformat(),
        'current_step': self.current_step,
        'steps': {},
      }

      for step_id, step in self.steps.items():
        step_dict = asdict(step)
        step_dict['status'] = step.status.value  # Convert enum to string
        data['steps'][step_id] = step_dict

      with open(self.progress_file, 'w') as f:
        json.dump(data, f, indent=2)

    except Exception as e:
      print(f'⚠️  Could not save progress: {e}')

  def start_step(self, step_id: str) -> bool:
    """Start a setup step.

    Args:
        step_id: ID of the step to start

    Returns:
        True if step can be started, False if dependencies not met
    """
    if step_id not in self.steps:
      raise ValueError(f'Unknown step: {step_id}')

    step = self.steps[step_id]

    # Check if already completed
    if step.status == StepStatus.COMPLETED:
      print(f"⏭️  Step '{step.name}' already completed - skipping")
      return False

    # Check dependencies
    for dep_id in step.dependencies:
      if dep_id not in self.steps:
        print(f'❌ Unknown dependency: {dep_id}')
        return False

      dep_step = self.steps[dep_id]
      if dep_step.status != StepStatus.COMPLETED:
        print(f"❌ Cannot start '{step.name}' - dependency '{dep_step.name}' not completed")
        return False

    # Start the step
    step.status = StepStatus.IN_PROGRESS
    step.start_time = datetime.now().isoformat()
    step.end_time = None
    step.duration_seconds = None
    step.error_message = None

    self.current_step = step_id

    print(f'🚀 Starting: {step.name}')
    print(f'   {step.description}')

    self._save_progress()
    return True

  def complete_step(self, step_id: str, result_data: Optional[Dict[str, Any]] = None):
    """Mark a step as completed.

    Args:
        step_id: ID of the step to complete
        result_data: Optional data to store with the result
    """
    if step_id not in self.steps:
      raise ValueError(f'Unknown step: {step_id}')

    step = self.steps[step_id]

    if step.status != StepStatus.IN_PROGRESS:
      print(f"⚠️  Step '{step.name}' is not in progress")
      return

    # Complete the step
    step.status = StepStatus.COMPLETED
    step.end_time = datetime.now().isoformat()
    step.result_data = result_data

    # Calculate duration
    if step.start_time:
      start = datetime.fromisoformat(step.start_time)
      end = datetime.fromisoformat(step.end_time)
      step.duration_seconds = (end - start).total_seconds()

    self.current_step = None

    print(f'✅ Completed: {step.name}')
    if step.duration_seconds:
      print(f'   Duration: {step.duration_seconds:.1f}s')

    self._save_progress()

  def fail_step(self, step_id: str, error_message: str):
    """Mark a step as failed.

    Args:
        step_id: ID of the step that failed
        error_message: Error message describing the failure
    """
    if step_id not in self.steps:
      raise ValueError(f'Unknown step: {step_id}')

    step = self.steps[step_id]

    step.status = StepStatus.FAILED
    step.end_time = datetime.now().isoformat()
    step.error_message = error_message

    # Calculate duration
    if step.start_time:
      start = datetime.fromisoformat(step.start_time)
      end = datetime.fromisoformat(step.end_time)
      step.duration_seconds = (end - start).total_seconds()

    self.current_step = None

    print(f'❌ Failed: {step.name}')
    print(f'   Error: {error_message}')

    self._save_progress()

  def skip_step(self, step_id: str, reason: str):
    """Mark a step as skipped.

    Args:
        step_id: ID of the step to skip
        reason: Reason for skipping
    """
    if step_id not in self.steps:
      raise ValueError(f'Unknown step: {step_id}')

    step = self.steps[step_id]
    step.status = StepStatus.SKIPPED
    step.error_message = f'Skipped: {reason}'

    print(f'⏭️  Skipped: {step.name}')
    print(f'   Reason: {reason}')

    self._save_progress()

  def get_next_step(self) -> Optional[str]:
    """Get the next step that should be executed.

    Returns:
        Step ID of next step, or None if all done
    """
    for step_id, step in self.steps.items():
      if step.status in [StepStatus.PENDING, StepStatus.FAILED]:
        # Check if dependencies are met
        deps_met = all(
          self.steps[dep_id].status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
          for dep_id in step.dependencies
        )
        if deps_met:
          return step_id

    return None

  def get_completed_steps(self) -> List[str]:
    """Get list of completed step IDs."""
    return [step_id for step_id, step in self.steps.items() if step.status == StepStatus.COMPLETED]

  def get_failed_steps(self) -> List[str]:
    """Get list of failed step IDs."""
    return [step_id for step_id, step in self.steps.items() if step.status == StepStatus.FAILED]

  def is_setup_complete(self) -> bool:
    """Check if entire setup is complete."""
    return all(
      step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for step in self.steps.values()
    )

  def _show_progress_summary(self):
    """Show a summary of current progress."""
    total_steps = len(self.steps)
    completed = len([s for s in self.steps.values() if s.status == StepStatus.COMPLETED])
    failed = len([s for s in self.steps.values() if s.status == StepStatus.FAILED])
    skipped = len([s for s in self.steps.values() if s.status == StepStatus.SKIPPED])

    print(f'📊 Progress Summary: {completed}/{total_steps} completed')
    if failed > 0:
      print(f'   ❌ {failed} failed steps')
    if skipped > 0:
      print(f'   ⏭️  {skipped} skipped steps')

  def show_detailed_progress(self):
    """Show detailed progress for all steps."""
    print('\n📋 Detailed Setup Progress')
    print('=' * 50)

    for step_id, step in self.steps.items():
      status_icon = {
        StepStatus.PENDING: '⏳',
        StepStatus.IN_PROGRESS: '🚀',
        StepStatus.COMPLETED: '✅',
        StepStatus.FAILED: '❌',
        StepStatus.SKIPPED: '⏭️',
      }.get(step.status, '❓')

      print(f'{status_icon} {step.name}')
      print(f'    {step.description}')

      if step.status == StepStatus.COMPLETED and step.duration_seconds:
        print(f'    Duration: {step.duration_seconds:.1f}s')
      elif step.status == StepStatus.FAILED and step.error_message:
        print(f'    Error: {step.error_message}')
      elif step.status == StepStatus.SKIPPED and step.error_message:
        print(f'    {step.error_message}')

      print()

    self._show_progress_summary()

  def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
    """Get result data from a completed step.

    Args:
        step_id: ID of the step

    Returns:
        Result data if available, None otherwise
    """
    if step_id in self.steps:
      return self.steps[step_id].result_data
    return None

  def reset_step(self, step_id: str):
    """Reset a step to pending status.

    Args:
        step_id: ID of the step to reset
    """
    if step_id not in self.steps:
      raise ValueError(f'Unknown step: {step_id}')

    step = self.steps[step_id]
    step.status = StepStatus.PENDING
    step.start_time = None
    step.end_time = None
    step.duration_seconds = None
    step.error_message = None
    step.result_data = None

    print(f'🔄 Reset step: {step.name}')
    self._save_progress()

  def reset_all_steps(self):
    """Reset all steps to pending status."""
    for step_id in self.steps:
      self.reset_step(step_id)

    self.current_step = None
    print('🔄 Reset all steps to pending')

  def cleanup_progress_file(self):
    """Remove the progress file."""
    if self.progress_file.exists():
      self.progress_file.unlink()
      print(f'🧹 Removed progress file: {self.progress_file}')

  def export_progress_report(self, output_file: Optional[Path] = None) -> str:
    """Export a detailed progress report.

    Args:
        output_file: Optional file to write report to

    Returns:
        Report content as string
    """
    report_lines = [
      'MLflow Demo Setup Progress Report',
      '=' * 40,
      f'Session ID: {self.session_id}',
      f'Generated: {datetime.now().isoformat()}',
      '',
    ]

    # Summary
    total_steps = len(self.steps)
    completed = len([s for s in self.steps.values() if s.status == StepStatus.COMPLETED])
    failed = len([s for s in self.steps.values() if s.status == StepStatus.FAILED])

    report_lines.extend(
      [
        'Summary:',
        f'  Total Steps: {total_steps}',
        f'  Completed: {completed}',
        f'  Failed: {failed}',
        f'  Success Rate: {(completed / total_steps) * 100:.1f}%',
        '',
      ]
    )

    # Detailed step information
    report_lines.append('Detailed Steps:')
    for step_id, step in self.steps.items():
      report_lines.append(f'  {step.name} ({step.status.value})')
      if step.duration_seconds:
        report_lines.append(f'    Duration: {step.duration_seconds:.1f}s')
      if step.error_message:
        report_lines.append(f'    Error: {step.error_message}')

    report_content = '\n'.join(report_lines)

    if output_file:
      with open(output_file, 'w') as f:
        f.write(report_content)
      print(f'📄 Progress report saved to: {output_file}')

    return report_content
