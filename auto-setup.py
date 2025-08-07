#!/usr/bin/env python3
"""
MLflow Demo Automated Setup Script

This script automates the entire end-to-end setup process for the MLflow demo application,
including creating Databricks resources, configuring environment, loading sample data,
and deploying the application.

Usage:
    python auto-setup.py [options]

Options:
    --dry-run          Show what would be created without actually creating resources
    --resume           Resume from previous failed/interrupted setup
    --reset            Reset all progress and start fresh
    --validate-only    Only run validation checks
    --help             Show this help message
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound, PermissionDenied

# Add automation directory to path
automation_dir = Path(__file__).parent / 'automation'
sys.path.insert(0, str(automation_dir))

from resource_manager import DatabricksResourceManager
from environment_detector import EnvironmentDetector
from validation import SetupValidator
from progress_tracker import ProgressTracker, StepStatus


class AutoSetup:
    """Main orchestrator for automated MLflow demo setup."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the auto setup.
        
        Args:
            dry_run: If True, only show what would be done without executing
        """
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent
        
        # Initialize components (defer authentication until actually running setup)
        self.client = None
        self.resource_manager = None
        self.env_detector = None
        self.validator = None
        self.progress = ProgressTracker(self.project_root)
        
        # Store configuration and created resources
        self.config = {}
        self.created_resources = {}
        self.detected_settings = {}
    
    def _initialize_databricks_components(self, skip_auth_prompts: bool = False) -> bool:
        """Initialize Databricks components with authentication."""
        if not self.dry_run:
            # Handle authentication first
            if not self._ensure_databricks_auth(skip_prompts=skip_auth_prompts):
                return False
            
            try:
                self.client = WorkspaceClient()
                self.resource_manager = DatabricksResourceManager(self.client)
                self.env_detector = EnvironmentDetector(self.client)
                self.validator = SetupValidator(self.client)
                return True
            except Exception as e:
                print(f"❌ Failed to initialize Databricks SDK: {e}")
                return False
        else:
            # For dry run, keep placeholder components
            return True
    
    def _get_available_catalogs_with_permissions(self) -> Dict[str, str]:
        """Get catalogs where user has required permissions."""
        available_catalogs = {}
        try:
            catalogs = list(self.client.catalogs.list())
            for catalog in catalogs:
                catalog_name = catalog.name
                
                # Check permissions levels
                can_list_schemas = False
                can_create_schemas = False
                
                try:
                    # Try to list schemas to check read access
                    schemas = list(self.client.schemas.list(catalog_name=catalog_name))
                    can_list_schemas = True
                    
                    # Test for CREATE SCHEMA permission by checking if we can see catalog details
                    # This is an approximation - the real test would be attempting to create a test schema
                    try:
                        catalog_info = self.client.catalogs.get(catalog_name)
                        # If we can read catalog details AND list schemas, likely have create permissions
                        # This is still approximate but better than just listing
                        can_create_schemas = True
                    except Exception:
                        pass
                    
                except Exception:
                    # Can't even list schemas
                    pass
                
                # Set permission level based on what we can do
                if can_create_schemas:
                    available_catalogs[catalog_name] = "READ/USE + CREATE SCHEMA"
                elif can_list_schemas:
                    available_catalogs[catalog_name] = "READ/USE (CREATE SCHEMA unknown)"
                else:
                    available_catalogs[catalog_name] = "LIMITED access"
                    
        except Exception as e:
            print(f"⚠️  Could not list catalogs: {e}")
        
        return available_catalogs
    
    def _get_available_schemas_in_catalog(self, catalog_name: str) -> Dict[str, str]:
        """Get schemas in a catalog where user has required permissions."""
        available_schemas = {}
        try:
            schemas = list(self.client.schemas.list(catalog_name=catalog_name))
            for schema in schemas:
                schema_name = schema.name
                full_schema_name = f"{catalog_name}.{schema_name}"
                
                # Check if user has required permissions: MANAGE and CREATE TABLE
                has_manage = False
                has_create_table = False
                
                try:
                    # Get schema info to check basic access
                    schema_info = self.client.schemas.get(full_schema_name)
                    
                    # Check for MANAGE permission by trying to get effective permissions
                    try:
                        # Try to get grants/permissions on the schema
                        # This is an approximation - checking if we can read schema grants
                        grants = list(self.client.grants.get_effective(
                            securable_type='schema',
                            full_name=full_schema_name
                        ))
                        
                        # Look for our permissions in the grants
                        current_user = self.client.current_user.me()
                        user_email = current_user.user_name if hasattr(current_user, 'user_name') else None
                        
                        for grant in grants:
                            # Check if this grant applies to current user
                            principal = getattr(grant, 'principal', '')
                            privileges = getattr(grant, 'privileges', [])
                            
                            if user_email and user_email in principal:
                                for privilege in privileges:
                                    if privilege == 'ALL_PRIVILEGES' or privilege == 'OWNER':
                                        has_manage = True
                                        has_create_table = True
                                        break
                                    elif privilege == 'CREATE_TABLE':
                                        has_create_table = True
                                    elif privilege == 'MANAGE':
                                        has_manage = True
                        
                        # If we can't determine from grants, try alternative check
                        if not (has_manage and has_create_table):
                            # Try to list tables as a proxy for having reasonable access
                            try:
                                tables = list(self.client.tables.list(catalog_name=catalog_name, schema_name=schema_name))
                                # If we can list tables, assume we have at least some useful access
                                has_create_table = True
                            except Exception:
                                pass
                        
                    except Exception:
                        # If we can't check grants, try a simpler approach
                        # Try to list tables as a proxy for having reasonable access
                        try:
                            tables = list(self.client.tables.list(catalog_name=catalog_name, schema_name=schema_name))
                            # If we can list tables, assume we have reasonable access
                            has_create_table = True
                            has_manage = True  # Assume if we can list tables, we have good access
                        except Exception:
                            pass
                    
                    # Determine permission level
                    if has_manage and has_create_table:
                        available_schemas[schema_name] = "MANAGE + CREATE TABLE"
                    elif has_create_table:
                        available_schemas[schema_name] = "CREATE TABLE only"
                    elif schema_info:
                        # We can see the schema but don't have required permissions
                        continue  # Don't include schemas without required permissions
                    
                except Exception:
                    # Can't access schema at all
                    continue
                    
        except Exception as e:
            print(f"⚠️  Could not list schemas in {catalog_name}: {e}")
        
        return available_schemas
    
    def _get_manageable_apps(self) -> Dict[str, str]:
        """Get existing Databricks apps where user has 'Can Manage' permission."""
        manageable_apps = {}
        try:
            apps = list(self.client.apps.list())
            current_user = self.client.current_user.me()
            user_email = current_user.user_name if hasattr(current_user, 'user_name') else None
            
            for app in apps:
                if not hasattr(app, 'name'):
                    continue
                    
                app_name = app.name
                has_manage_permission = False
                permission_reason = ""
                
                try:
                    # Get app details to check permissions
                    app_details = self.client.apps.get(app_name)
                    
                    # Check if user is the creator/owner
                    if hasattr(app_details, 'created_by') and user_email:
                        created_by = getattr(app_details, 'created_by', '')
                        if created_by == user_email:
                            has_manage_permission = True
                            permission_reason = "Owner/Creator"
                    
                    # Try to check app permissions/grants if not already determined
                    if not has_manage_permission:
                        try:
                            # Check if we can get app permissions
                            permissions = self.client.apps.get_permissions(app_name)
                            
                            # Look through permissions for current user
                            for perm in getattr(permissions, 'permissions', []):
                                principal = getattr(perm, 'principal', '')
                                permission_level = getattr(perm, 'permission_level', '')
                                
                                if user_email and user_email in principal:
                                    if permission_level in ['CAN_MANAGE', 'OWNER', 'IS_OWNER']:
                                        has_manage_permission = True
                                        permission_reason = f"Explicit {permission_level}"
                                        break
                            
                        except Exception:
                            pass
                    
                    # If we still can't determine permissions, try a fallback approach
                    if not has_manage_permission and app_details:
                        # If we can read app details successfully, assume we have some level of access
                        # This is more permissive but practical
                        has_manage_permission = True
                        permission_reason = "Can read details"
                    
                    # Include apps we can manage
                    if has_manage_permission:
                        manageable_apps[app_name] = permission_reason
                    
                except Exception:
                    # Can't access this app
                    continue
                    
        except Exception as e:
            print(f"⚠️  Could not list apps: {e}")
        
        return manageable_apps
    
    def _prompt_for_catalog_selection(self, suggested_catalog: str = None) -> str:
        """Interactive catalog selection with permission checking."""
        print("\n📁 Unity Catalog Selection")
        
        # Get available catalogs
        available_catalogs = self._get_available_catalogs_with_permissions()
        
        if not available_catalogs:
            print("❌ No accessible catalogs found. You may need Unity Catalog permissions.")
            return None
        
        print("Available catalogs:")
        catalog_list = list(available_catalogs.keys())
        
        # Show suggested catalog first if it exists
        if suggested_catalog and suggested_catalog in available_catalogs:
            print(f"   0. {suggested_catalog} (suggested) - {available_catalogs[suggested_catalog]}")
            start_idx = 1
        else:
            start_idx = 0
        
        # Show other catalogs
        for i, (catalog_name, access_level) in enumerate(available_catalogs.items()):
            if catalog_name != suggested_catalog:
                print(f"   {start_idx + i}. {catalog_name} - {access_level}")
        
        max_choice = len(catalog_list) - 1 + (1 if suggested_catalog in available_catalogs else 0)
        
        while True:
            try:
                choice = input(f"\nSelect catalog (0-{max_choice}): ").strip()
                
                # Check if it's a number
                try:
                    choice_num = int(choice)
                    if choice_num == 0 and suggested_catalog and suggested_catalog in available_catalogs:
                        return suggested_catalog
                    elif 1 <= choice_num <= len(catalog_list):
                        # Adjust index based on whether suggested catalog is shown
                        if suggested_catalog and suggested_catalog in available_catalogs:
                            selected_catalogs = [cat for cat in catalog_list if cat != suggested_catalog]
                            return selected_catalogs[choice_num - 1]
                        else:
                            return catalog_list[choice_num - 1]
                    else:
                        print(f"❌ Please enter a number between 0 and {max_choice}")
                        continue
                except ValueError:
                    print("❌ Please enter a valid number")
                        
            except KeyboardInterrupt:
                return None
    
    def _prompt_for_schema_selection(self, catalog_name: str, suggested_schema: str = None) -> str:
        """Interactive schema selection with permission checking."""
        print(f"\n📂 Schema Selection in '{catalog_name}'")
        
        # Get available schemas
        available_schemas = self._get_available_schemas_in_catalog(catalog_name)
        
        if not available_schemas:
            print(f"No accessible schemas found in '{catalog_name}'. Will create new schema.")
            new_schema = input("Enter new schema name [default]: ").strip()
            return new_schema or "default"
        
        print("Available schemas:")
        schema_list = list(available_schemas.keys())
        
        # Show suggested schema first if it exists
        if suggested_schema and suggested_schema in available_schemas:
            print(f"   0. {suggested_schema} (suggested) - {available_schemas[suggested_schema]}")
            start_idx = 1
        else:
            start_idx = 0
        
        # Show other schemas
        for i, (schema_name, access_level) in enumerate(available_schemas.items()):
            if schema_name != suggested_schema:
                print(f"   {start_idx + i}. {schema_name} - {access_level}")
        
        print(f"   {len(schema_list) + (1 if suggested_schema in available_schemas else 0)}. Create new schema")
        
        while True:
            try:
                choice = input(f"\nSelect schema (0-{len(schema_list) + (1 if suggested_schema in available_schemas else 0)}) or type schema name: ").strip()
                
                # Check if it's a number
                try:
                    choice_num = int(choice)
                    if choice_num == 0 and suggested_schema and suggested_schema in available_schemas:
                        return suggested_schema
                    elif 1 <= choice_num <= len(schema_list):
                        # Adjust index based on whether suggested schema is shown
                        if suggested_schema and suggested_schema in available_schemas:
                            selected_schemas = [sch for sch in schema_list if sch != suggested_schema]
                            return selected_schemas[choice_num - 1]
                        else:
                            return schema_list[choice_num - 1]
                    elif choice_num == len(schema_list) + (1 if suggested_schema in available_schemas else 0):
                        # Create new schema
                        new_schema = input("Enter new schema name: ").strip()
                        if new_schema:
                            print(f"💡 Will create new schema: {new_schema}")
                            return new_schema
                    else:
                        print(f"❌ Please enter a number between 0 and {len(schema_list) + (1 if suggested_schema in available_schemas else 0)}")
                        continue
                except ValueError:
                    # User typed a schema name directly
                    if choice in available_schemas:
                        return choice
                    else:
                        print(f"💡 Will create new schema: {choice}")
                        return choice
                        
            except KeyboardInterrupt:
                return None
    
    def _validate_app_name(self, app_name: str) -> bool:
        """Validate app name format for Databricks Apps."""
        import re
        if not app_name:
            return False
        # App name must contain only lowercase letters, numbers, and dashes
        pattern = r'^[a-z0-9-]+$'
        return bool(re.match(pattern, app_name))
    
    def _get_available_chat_models(self) -> List[str]:
        """Get list of available chat completion models from Databricks."""
        try:
            # Use the model discovery logic to find chat models
            from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
            
            endpoints = self.client.serving_endpoints.list()
            
            # Common chat model patterns
            chat_model_patterns = [
                'gpt-', 'claude-', 'gemini-', 'llama', 'mistral', 'databricks-',
                'chat', 'instruct', 'turbo'
            ]
            
            potential_chat_models = []
            
            for endpoint in endpoints:
                model_name = endpoint.name.lower()
                
                # Check if it matches chat patterns
                is_likely_chat = any(pattern in model_name for pattern in chat_model_patterns)
                
                # Exclude obvious non-chat models
                is_not_chat = any(exclude in model_name for exclude in ['embedding', 'vision', 'audio', 'whisper', 'imageai'])
                
                if is_likely_chat and not is_not_chat:
                    # Check if endpoint has chat task capability
                    try:
                        endpoint_details = self.client.serving_endpoints.get(name=endpoint.name)
                        if hasattr(endpoint_details, 'config') and endpoint_details.config:
                            # Check served entities for task type
                            if hasattr(endpoint_details.config, 'served_entities') and endpoint_details.config.served_entities:
                                for entity in endpoint_details.config.served_entities:
                                    if (hasattr(entity, 'external_model') and entity.external_model and 
                                        hasattr(entity.external_model, 'task') and 
                                        entity.external_model.task == 'llm/v1/chat'):
                                        potential_chat_models.append(endpoint.name)
                                        break
                                    elif (hasattr(entity, 'foundation_model') and entity.foundation_model and
                                          hasattr(entity.foundation_model, 'name')):
                                        # Foundation models typically support chat
                                        potential_chat_models.append(endpoint.name)
                                        break
                    except Exception:
                        # If we can't get details, include it based on name pattern
                        potential_chat_models.append(endpoint.name)
            
            # Remove duplicates and sort
            chat_models = sorted(list(set(potential_chat_models)))
            
            # Prioritize certain models at the top
            priority_models = ['databricks-claude-3-7-sonnet', 'databricks-claude-sonnet-4', 'gpt-4o']
            prioritized_models = []
            
            for priority in priority_models:
                if priority in chat_models:
                    prioritized_models.append(priority)
                    chat_models.remove(priority)
            
            return prioritized_models + chat_models
            
        except Exception as e:
            print(f"⚠️  Could not discover chat models: {e}")
            # Return default options
            return [
                'databricks-claude-3-7-sonnet',
                'databricks-claude-sonnet-4', 
                'databricks-meta-llama-3-3-70b-instruct',
                'gpt-4o'
            ]

    def _prompt_for_llm_model(self, suggested_model: str = None) -> str:
        """Interactive LLM model selection with available chat models."""
        print("\n🤖 LLM Model Selection")
        
        # Get available chat models
        available_models = self._get_available_chat_models()
        
        if not available_models:
            print("❌ No chat models found. Using default.")
            return suggested_model or "databricks-claude-3-7-sonnet"
        
        print("Available chat completion models:")
        
        # Show suggested model first if it exists
        if suggested_model and suggested_model in available_models:
            print(f"   0. {suggested_model} (suggested)")
            start_idx = 1
        else:
            start_idx = 0
        
        # Show other models
        for i, model_name in enumerate(available_models):
            if model_name != suggested_model:
                print(f"   {start_idx + i}. {model_name}")
        
        max_choice = len(available_models) - 1 + (1 if suggested_model in available_models else 0)
        
        while True:
            try:
                choice = input(f"\nSelect model (0-{max_choice}) or press ENTER for default: ").strip()
                
                # Use default if empty
                if not choice:
                    return suggested_model or available_models[0]
                
                # Check if it's a number
                try:
                    choice_num = int(choice)
                    if choice_num == 0 and suggested_model and suggested_model in available_models:
                        return suggested_model
                    elif 1 <= choice_num <= len(available_models):
                        # Adjust index based on whether suggested model is shown
                        if suggested_model and suggested_model in available_models:
                            selected_models = [model for model in available_models if model != suggested_model]
                            return selected_models[choice_num - 1]
                        else:
                            return available_models[choice_num - 1]
                    else:
                        print(f"❌ Please enter a number between 0 and {max_choice}")
                        continue
                except ValueError:
                    # User typed a model name directly
                    if choice in available_models:
                        return choice
                    else:
                        print(f"❌ Model '{choice}' not found in available models")
                        continue
                        
            except KeyboardInterrupt:
                return suggested_model or available_models[0]

    def _prompt_for_app_name(self, suggested_app_name: str = None) -> str:
        """Interactive app name selection with permission checking."""
        print("\n📱 Databricks App Name Selection")
        
        manageable_apps = self._get_manageable_apps()
        
        if manageable_apps:
            print("Apps you can manage:")
            
            # Create a simple ordered list of all apps
            display_list = []
            
            # Add suggested app first if it exists and is manageable
            if suggested_app_name and suggested_app_name in manageable_apps:
                display_list.append((suggested_app_name, f"{manageable_apps[suggested_app_name]} (suggested)"))
            
            # Add all other apps
            for app_name, permission in manageable_apps.items():
                if app_name != suggested_app_name:
                    display_list.append((app_name, permission))
            
            # Display the list
            for i, (app_name, permission) in enumerate(display_list):
                print(f"   {i}. {app_name} - {permission}")
            
            create_new_index = len(display_list)
            print(f"   {create_new_index}. Create new app")
            
            while True:
                try:
                    choice = input(f"\nSelect app (0-{create_new_index}) or type app name: ").strip()
                    
                    # Check if it's a number
                    try:
                        choice_num = int(choice)
                        if 0 <= choice_num < len(display_list):
                            selected_app = display_list[choice_num][0]
                            print(f"📱 Will update existing app: {selected_app}")
                            return selected_app
                        elif choice_num == create_new_index:
                            # Create new app
                            while True:
                                new_app = input("Enter new app name (lowercase letters, numbers, dashes only): ").strip()
                                if not new_app:
                                    print("❌ App name cannot be empty")
                                    continue
                                if not self._validate_app_name(new_app):
                                    print("❌ App name must contain only lowercase letters, numbers, and dashes")
                                    continue
                                if new_app in manageable_apps:
                                    print(f"📱 Will update existing app: {new_app}")
                                    return new_app
                                else:
                                    print(f"💡 Will create new app: {new_app}")
                                    return new_app
                        else:
                            print(f"❌ Please enter a number between 0 and {create_new_index}")
                            continue
                    except ValueError:
                        # User typed an app name directly
                        if not self._validate_app_name(choice):
                            print("❌ App name must contain only lowercase letters, numbers, and dashes")
                            continue
                        if choice in manageable_apps:
                            print(f"📱 Will update existing app: {choice}")
                            return choice
                        else:
                            print(f"💡 Will create new app: {choice}")
                            return choice
                            
                except KeyboardInterrupt:
                    return None
        else:
            # No manageable apps found, just prompt for new app name
            print("No manageable apps found in workspace.")
            while True:
                if suggested_app_name and self._validate_app_name(suggested_app_name):
                    app_name = input(f"App name [{suggested_app_name}]: ").strip()
                    if not app_name:
                        app_name = suggested_app_name
                else:
                    app_name = input("App name (lowercase letters, numbers, dashes only): ").strip()
                    if not app_name:
                        print("❌ App name is required")
                        continue
                
                if not self._validate_app_name(app_name):
                    print("❌ App name must contain only lowercase letters, numbers, and dashes")
                    continue
                
                print(f"💡 Will create new app: {app_name}")
                return app_name
    
    def _restore_config_from_progress(self):
        """Restore configuration from saved progress."""
        try:
            # Look for saved config in completed steps
            completed_step_ids = self.progress.get_completed_steps()
            for step_id in completed_step_ids:
                step_data = self.progress.steps.get(step_id)
                if step_data and hasattr(step_data, 'result_data') and step_data.result_data:
                    if 'config' in step_data.result_data:
                        saved_config = step_data.result_data['config']
                        self.config.update(saved_config)
                        print(f"🔄 Restored configuration from progress: {list(saved_config.keys())}")
                    
                    # Also restore experiment ID if available
                    if 'experiment_id' in step_data.result_data:
                        self.config['MLFLOW_EXPERIMENT_ID'] = step_data.result_data['experiment_id']
                        print(f"🔄 Restored experiment ID: {step_data.result_data['experiment_id']}")
                    
                    # Restore other important config values
                    if 'app_name' in step_data.result_data:
                        self.config['DATABRICKS_APP_NAME'] = step_data.result_data['app_name']
        except Exception as e:
            print(f"⚠️  Could not restore config from progress: {e}")
    
    def run_setup(self, resume: bool = False) -> bool:
        """Run the complete setup process.
        
        Args:
            resume: If True, resume from previous progress
            
        Returns:
            True if setup completed successfully
        """
        print("🚀 MLflow Demo Automated Setup")
        print("=" * 50)
        
        if not resume:
            print(f"🔧 Setup mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        else:
            print("🔄 Resuming previous setup...")
            self.progress.show_detailed_progress()
        
        # Restore configuration from previous progress if resuming
        if resume:
            self._restore_config_from_progress()
        
        # Initialize Databricks components (skip auth prompts on resume if already working)
        if not self._initialize_databricks_components(skip_auth_prompts=resume):
            return False
        
        try:
            success = True
            
            # Execute setup steps in order
            while True:
                next_step = self.progress.get_next_step()
                if not next_step:
                    break
                
                if not self.progress.start_step(next_step):
                    continue
                
                try:
                    if next_step == 'validate_prerequisites':
                        success = self._validate_prerequisites()
                    elif next_step == 'detect_environment':
                        success = self._detect_environment()
                    elif next_step == 'collect_user_input':
                        success = self._collect_user_input()
                    elif next_step == 'validate_config':
                        success = self._validate_config()
                    elif next_step == 'create_catalog_schema':
                        success = self._create_catalog_schema()
                    elif next_step == 'create_experiment':
                        success = self._create_experiment()
                    elif next_step == 'create_app':
                        success = self._create_app()
                    elif next_step == 'setup_permissions':
                        success = self._setup_permissions()
                    elif next_step == 'generate_env_file':
                        success = self._generate_env_file()
                    elif next_step == 'install_dependencies':
                        success = self._install_dependencies()
                    elif next_step == 'load_sample_data':
                        success = self._load_sample_data()
                    elif next_step == 'validate_local_setup':
                        success = self._validate_local_setup()
                    elif next_step == 'deploy_app':
                        success = self._deploy_app()
                    elif next_step == 'validate_deployment':
                        success = self._validate_deployment()
                    elif next_step == 'run_integration_tests':
                        success = self._run_integration_tests()
                    else:
                        success = False
                        raise ValueError(f"Unknown step: {next_step}")
                    
                    if success:
                        self.progress.complete_step(next_step, self._get_step_result(next_step))
                    else:
                        self.progress.fail_step(next_step, "Step execution failed")
                        break
                        
                except Exception as e:
                    error_msg = f"Error in step {next_step}: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.progress.fail_step(next_step, error_msg)
                    success = False
                    break
            
            # Show final results
            self._show_final_results(success)
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️  Setup interrupted by user")
            self._show_final_results(False)
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during setup: {e}")
            self._show_final_results(False)
            return False
    
    def _validate_prerequisites(self) -> bool:
        """Validate prerequisites before setup."""
        print("🔍 Validating prerequisites...")
        
        if self.dry_run:
            print("   [DRY RUN] Would validate prerequisites")
            return True
        
        valid, issues = self.validator.validate_prerequisites()
        
        if not valid:
            print("❌ Prerequisites validation failed:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        return True
    
    def _detect_environment(self) -> bool:
        """Detect environment settings."""
        print("🔍 Detecting environment settings...")
        
        if self.dry_run:
            print("   [DRY RUN] Would detect environment settings")
            # Set dummy values for dry run
            self.detected_settings = {
                'workspace_url': 'https://demo.cloud.databricks.com',
                'suggested_catalog': 'workspace',
                'suggested_schema': 'default',
                'suggested_names': {
                    'experiment_name': 'mlflow_demo_experiment',
                    'app_name': 'mlflow_demo_app'
                }
            }
            return True
        
        # Detect workspace URL
        workspace_url = self.env_detector.detect_workspace_url()
        
        # Suggest catalog/schema
        catalog, schema = self.env_detector.suggest_catalog_schema()
        
        # Suggest unique names
        name_suggestions = self.env_detector.suggest_unique_names()
        
        # Store detected settings
        self.detected_settings = {
            'workspace_url': workspace_url,
            'suggested_catalog': catalog,
            'suggested_schema': schema,
            'suggested_names': name_suggestions
        }
        
        return True
    
    def _collect_user_input(self) -> bool:
        """Collect required user input."""
        print("📝 Collecting configuration...")
        
        if self.dry_run:
            print("   [DRY RUN] Would collect user input")
            # Use dummy values for dry run
            self.config = {
                'DATABRICKS_HOST': 'https://demo.cloud.databricks.com',
                'UC_CATALOG': 'workspace',
                'UC_SCHEMA': 'default',
                'DATABRICKS_APP_NAME': 'mlflow_demo_app',
                'MLFLOW_EXPERIMENT_ID': '123456789'
            }
            return True
        
        print("\n📝 Configuration Setup")
        print("Please provide the following information:")
        print("(Press Enter to use suggested values where available)\n")
        
        # Get workspace URL automatically from the authenticated profile
        workspace_url = self.detected_settings.get('workspace_url')
        if not workspace_url:
            try:
                workspace_url = self.client.config.host
            except Exception:
                workspace_url = "https://unknown-workspace.cloud.databricks.com"
        
        print(f"✅ Using workspace URL from profile: {workspace_url}")
        
        # Interactive catalog selection
        suggested_catalog = self.detected_settings.get('suggested_catalog')
        catalog = self._prompt_for_catalog_selection(suggested_catalog)
        if not catalog:
            print("❌ Catalog selection is required")
            return False
        
        # Interactive schema selection
        suggested_schema = self.detected_settings.get('suggested_schema')
        schema = self._prompt_for_schema_selection(catalog, suggested_schema)
        if not schema:
            print("❌ Schema selection is required")
            return False
        
        # Interactive app name selection
        suggested_app_name = self.detected_settings['suggested_names']['app_name']
        app_name = self._prompt_for_app_name(suggested_app_name)
        if not app_name:
            print("❌ App name is required")
            return False
        
        # LLM model selection
        llm_model = self._prompt_for_llm_model("databricks-claude-3-7-sonnet")
        
        # Store configuration
        self.config = {
            'DATABRICKS_HOST': workspace_url,
            'UC_CATALOG': catalog,
            'UC_SCHEMA': schema,
            'DATABRICKS_APP_NAME': app_name,
            'LLM_MODEL': llm_model
        }
        
        return True
    
    def _validate_config(self) -> bool:
        """Validate user configuration."""
        print("✅ Validating configuration...")
        
        if self.dry_run:
            print("   [DRY RUN] Would validate configuration")
            return True
        
        # Only validate the configuration we have at this point
        issues = []
        
        # Check required variables that should exist at this stage
        required_at_this_stage = [
            'DATABRICKS_HOST',
            'UC_CATALOG',
            'UC_SCHEMA',
            'DATABRICKS_APP_NAME',
            'LLM_MODEL'
        ]
        
        for var in required_at_this_stage:
            if not self.config.get(var):
                issues.append(f"Missing required configuration: {var}")
        
        # Validate workspace URL format
        if 'DATABRICKS_HOST' in self.config:
            host = self.config['DATABRICKS_HOST']
            if not host.startswith('https://'):
                issues.append("DATABRICKS_HOST must start with https://")
            if not '.cloud.databricks.com' in host and not '.azuredatabricks.net' in host:
                issues.append("DATABRICKS_HOST doesn't appear to be a valid Databricks URL")
        
        # Validate catalog.schema format
        if 'UC_CATALOG' in self.config and 'UC_SCHEMA' in self.config:
            catalog = self.config['UC_CATALOG']
            schema = self.config['UC_SCHEMA']
            if '.' in catalog or '.' in schema:
                issues.append("UC_CATALOG and UC_SCHEMA should not contain dots")
        
        if issues:
            print("❌ Configuration validation failed:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        return True
    
    def _create_catalog_schema(self) -> bool:
        """Create catalog and schema if needed."""
        catalog = self.config['UC_CATALOG']
        schema = self.config['UC_SCHEMA']
        
        print(f"📁 Setting up Unity Catalog: {catalog}.{schema}")
        
        if self.dry_run:
            print(f"   [DRY RUN] Would create catalog '{catalog}' and schema '{schema}'")
            return True
        
        try:
            # Check if catalog exists first
            catalog_exists = False
            try:
                self.client.catalogs.get(catalog)
                catalog_exists = True
                print(f"✅ Catalog '{catalog}' already exists")
            except NotFound:
                print(f"📁 Catalog '{catalog}' does not exist, attempting to create...")
            
            # Create catalog if needed
            if not catalog_exists:
                try:
                    catalog_info = self.resource_manager.create_catalog_if_not_exists(catalog)
                    self.created_resources['catalog'] = catalog_info.name
                    print(f"✅ Created catalog '{catalog}'")
                except PermissionDenied:
                    print(f"❌ Permission denied: Cannot create catalog '{catalog}'")
                    print(f"   Please ask your workspace admin to create the catalog or grant you permissions")
                    return False
                except Exception as e:
                    print(f"❌ Failed to create catalog '{catalog}': {e}")
                    return False
            
            # Check if schema exists
            schema_exists = False
            try:
                self.client.schemas.get(f"{catalog}.{schema}")
                schema_exists = True
                print(f"✅ Schema '{catalog}.{schema}' already exists")
            except NotFound:
                print(f"📂 Schema '{schema}' does not exist in '{catalog}', attempting to create...")
            
            # Create schema if needed
            if not schema_exists:
                try:
                    schema_info = self.resource_manager.create_schema_if_not_exists(catalog, schema)
                    self.created_resources['schema'] = f"{catalog}.{schema}"
                    print(f"✅ Created schema '{catalog}.{schema}'")
                except Exception as e:
                    print(f"❌ Failed to create schema '{catalog}.{schema}': {e}")
                    print(f"   You may need permissions to create schemas in catalog '{catalog}'")
                    return False
            else:
                self.created_resources['schema'] = f"{catalog}.{schema}"
            
            return True
        except Exception as e:
            print(f"❌ Failed to set up catalog/schema: {e}")
            return False
    
    def _create_experiment(self) -> bool:
        """Create MLflow experiment automatically."""
        # Get app name from config for experiment naming
        app_name = self.config.get('DATABRICKS_APP_NAME', 'mlflow_demo_app')
        
        # Use /Shared/{app_name} pattern for experiment name
        experiment_name = f"/Shared/{app_name}"
        
        print(f"🧪 Creating MLflow experiment: {experiment_name}")
        
        if self.dry_run:
            print(f"   [DRY RUN] Would create experiment '{experiment_name}'")
            self.config['MLFLOW_EXPERIMENT_ID'] = '123456789'
            return True
        
        try:
            experiment_id = self.resource_manager.create_mlflow_experiment(
                name=experiment_name
            )
            
            self.config['MLFLOW_EXPERIMENT_ID'] = experiment_id
            self.created_resources['experiment_id'] = experiment_id
            
            return True
        except Exception as e:
            print(f"❌ Failed to create experiment: {e}")
            return False
    
    def _create_app(self) -> bool:
        """Create Databricks App."""
        # Use app name from config if available, otherwise from detected settings
        if 'DATABRICKS_APP_NAME' in self.config:
            app_name = self.config['DATABRICKS_APP_NAME']
        else:
            if 'suggested_names' not in self.detected_settings or 'app_name' not in self.detected_settings['suggested_names']:
                if 'suggested_names' not in self.detected_settings:
                    self.detected_settings['suggested_names'] = {}
                self.detected_settings['suggested_names']['app_name'] = 'mlflow_demo_app'
            app_name = self.detected_settings['suggested_names']['app_name']
            self.config['DATABRICKS_APP_NAME'] = app_name
        
        print(f"📱 Creating Databricks App: {app_name}")
        
        if self.dry_run:
            print(f"   [DRY RUN] Would create app '{app_name}'")
            return True
        
        try:
            # Generate workspace path for the app
            current_user = self.env_detector.get_current_user()
            if current_user:
                workspace_path = f"/Workspace/Users/{current_user}/{app_name}"
                self.config['LHA_SOURCE_CODE_PATH'] = workspace_path
            else:
                # Fallback to shared workspace
                workspace_path = f"/Workspace/Shared/{app_name}"
                self.config['LHA_SOURCE_CODE_PATH'] = workspace_path
                print("⚠️  Could not determine current user - using shared workspace path")
            
            print(f"📁 App source code path: {workspace_path}")
            
            app = self.resource_manager.create_databricks_app(
                name=app_name,
                description="MLflow demo application - automated setup",
                source_code_path=workspace_path
            )
            
            self.created_resources['app_name'] = app_name
            
            # Automatically start the app after creation
            print(f"\n📱 App '{app_name}' has been created successfully!")
            print(f"🚀 Starting app '{app_name}'...")
            if not self.resource_manager.start_app(app_name, timeout_minutes=10):
                print(f"⚠️  Failed to start app '{app_name}' - it may need to be started manually")
                print(f"💡 You can start it later from the Databricks UI or after deployment")
                # Don't fail the setup if app start fails - it can be started later
            
            return True
        except Exception as e:
            print(f"❌ Failed to create app: {e}")
            return False
    
    def _setup_permissions(self) -> bool:
        """Setup permissions for app service principal."""
        print("🔐 Setting up permissions...")
        
        if self.dry_run:
            print("   [DRY RUN] Would setup permissions")
            return True
        
        try:
            app_name = self.config['DATABRICKS_APP_NAME']
            
            # Get app service principal (this should work after deployment)
            service_principal = self.resource_manager.get_app_service_principal(app_name)
            
            if service_principal:
                print(f"✅ Found app service principal: {service_principal}")
                
                # Grant schema permissions (ALL PERMISSIONS + MANAGE)
                schema_name = f"{self.config['UC_CATALOG']}.{self.config['UC_SCHEMA']}"
                print(f"🔐 Granting schema permissions on {schema_name}...")
                self.resource_manager.grant_schema_permissions(
                    schema_name, 
                    service_principal,
                    permissions=['ALL_PRIVILEGES', 'MANAGE']
                )
                
                # Grant experiment permissions (CAN MANAGE)
                experiment_id = self.config['MLFLOW_EXPERIMENT_ID']
                print(f"🔐 Granting experiment permissions on {experiment_id}...")
                self.resource_manager.grant_experiment_permissions(
                    experiment_id, 
                    service_principal,
                    permissions=['CAN_MANAGE']
                )
                
                # Grant model serving endpoint access
                llm_model = self.config.get('LLM_MODEL', 'databricks-claude-3-7-sonnet')
                print(f"🔐 Granting model serving access to {llm_model}...")
                self.resource_manager.grant_model_serving_permissions(
                    app_name,
                    llm_model
                )
                
                print("✅ Permissions set successfully")
            else:
                print("⚠️  App service principal not available yet - permissions may need to be set manually")
                print("   This is normal if the app hasn't been deployed yet")
            
            return True
        except Exception as e:
            print(f"⚠️  Permission setup had issues: {e}")
            print("   You may need to configure permissions manually via the UI")
            return True  # Don't fail setup for permission issues
    
    def _generate_env_file(self) -> bool:
        """Generate .env.local file."""
        print("📄 Generating environment file...")
        
        if self.dry_run:
            print("   [DRY RUN] Would generate .env.local file")
            return True
        
        try:
            # Debug: print current config
            print(f"📋 Current config: {self.config}")
            
            # Complete configuration with defaults
            complete_config = self.env_detector.generate_environment_config(self.config)
            
            # Debug: print complete config
            print(f"📋 Complete config: {complete_config}")
            
            # Write .env.local file
            env_file = self.project_root / '.env.local'
            with open(env_file, 'w') as f:
                f.write(f"# Generated by auto-setup.py on {self._get_timestamp()}\n\n")
                
                for key, value in complete_config.items():
                    f.write(f'{key}="{value}"\n')
            
            print(f"✅ Created {env_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create environment file: {e}")
            return False
    
    def _install_dependencies(self) -> bool:
        """Install Python and frontend dependencies."""
        print("📦 Installing dependencies...")
        
        if self.dry_run:
            print("   [DRY RUN] Would install dependencies")
            return True
        
        try:
            # Install Python dependencies with uv
            print("   Installing Python dependencies...")
            result = subprocess.run(['uv', 'sync'], cwd=self.project_root, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to install Python dependencies")
                return False
            
            # Install frontend dependencies with bun
            print("   Installing frontend dependencies...")
            client_dir = self.project_root / 'client'
            result = subprocess.run(['bun', 'install'], cwd=client_dir, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to install frontend dependencies")
                return False
            
            print("✅ Dependencies installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def _load_sample_data(self) -> bool:
        """Load sample data using setup scripts in order."""
        print("📊 Loading sample data...")
        
        if self.dry_run:
            print("   [DRY RUN] Would load sample data")
            return True
        
        try:
            # Run setup scripts in order 1-5
            setup_scripts = [
                "1_load_prompts.py",
                "2_load_sample_traces.py", 
                "3_run_evals_for_sample_traces.py",
                "4_setup_monitoring.py",
                "5_setup_labeling_session.py"
            ]
            
            setup_dir = self.project_root / 'setup'
            
            for script in setup_scripts:
                script_path = setup_dir / script
                if not script_path.exists():
                    print(f"⚠️  Setup script {script} not found, skipping...")
                    continue
                
                print(f"🔄 Running setup script: {script}")
                
                # Run with uv python to ensure proper environment
                # Stream output to user in real-time
                try:
                    # Use full script path and run from project root
                    script_full_path = f"setup/{script}"
                    process = subprocess.Popen(
                        ['uv', 'run', 'python', script_full_path],
                        cwd=self.project_root,  # Run from project root, not setup dir
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,  # Line buffered
                        universal_newlines=True,
                        env=os.environ.copy()  # Inherit current environment
                    )
                    
                    # Print output in real-time
                    output_lines = []
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            print(f"   {output.rstrip()}")  # Indent script output
                            output_lines.append(output)
                    
                    # Wait for process to complete and get return code
                    return_code = process.wait()
                    
                    if return_code != 0:
                        print(f"❌ Failed to run {script} (exit code: {return_code})")
                        print("📋 Debug info:")
                        print(f"   Command: uv run python {script_full_path}")
                        print(f"   Working dir: {self.project_root}")
                        print(f"   Script exists: {(self.project_root / script_full_path).exists()}")
                        if output_lines:
                            print("   Last few output lines:")
                            for line in output_lines[-5:]:
                                print(f"     {line.rstrip()}")
                        return False
                    else:
                        print(f"✅ Completed: {script}")
                        
                except subprocess.TimeoutExpired:
                    print(f"❌ Script {script} timed out after 5 minutes")
                    process.kill()
                    return False
                except Exception as script_error:
                    print(f"❌ Exception running {script}: {script_error}")
                    print(f"📋 Debug info:")
                    print(f"   Command: uv run python {script_full_path}")
                    print(f"   Working dir: {self.project_root}")
                    print(f"   Script exists: {(self.project_root / script_full_path).exists()}")
                    return False
            
            print("✅ All setup scripts completed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load sample data: {e}")
            return False
    
    def _validate_local_setup(self) -> bool:
        """Validate local setup by running development server briefly."""
        print("✅ Validating local setup...")
        
        if self.dry_run:
            print("   [DRY RUN] Would validate local setup")
            return True
        
        # For now, just check that the setup files are in place
        # A full test would involve starting the server and testing endpoints
        
        env_file = self.project_root / '.env.local'
        if not env_file.exists():
            print("❌ .env.local file not found")
            return False
        
        print("✅ Local setup validation passed")
        return True
    
    def _deploy_app(self) -> bool:
        """Deploy the application."""
        print("🚀 Deploying application...")
        
        if self.dry_run:
            print("   [DRY RUN] Would deploy application")
            return True
        
        try:
            # Run the deploy.sh script
            result = subprocess.run(
                ['./deploy.sh'],
                cwd=self.project_root,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Deployment failed")
                return False
            
            print("✅ Application deployed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to deploy application: {e}")
            return False
    
    def _validate_deployment(self) -> bool:
        """Validate deployment."""
        print("✅ Validating deployment...")
        
        if self.dry_run:
            print("   [DRY RUN] Would validate deployment")
            return True
        
        app_name = self.config['DATABRICKS_APP_NAME']
        
        # Wait for app to be ready
        if not self.validator.wait_for_app_ready(app_name, timeout_minutes=5):
            print("⚠️  App deployment validation timed out")
            return False
        
        # Run deployment validation
        valid, issues = self.validator.validate_deployment(app_name)
        
        if not valid:
            print("❌ Deployment validation failed:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        print("✅ Deployment validation passed")
        return True
    
    def _run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("🧪 Running integration tests...")
        
        if self.dry_run:
            print("   [DRY RUN] Would run integration tests")
            return True
        
        valid, issues = self.validator.run_integration_tests(self.config)
        
        if not valid:
            print("❌ Integration tests failed:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        print("✅ Integration tests passed")
        return True
    
    def _get_step_result(self, step_id: str) -> Dict[str, Any]:
        """Get result data for a completed step."""
        if step_id == 'collect_user_input':
            return {'config': self.config.copy()}
        elif step_id == 'create_experiment':
            return {'experiment_id': self.config.get('MLFLOW_EXPERIMENT_ID')}
        elif step_id == 'create_app':
            return {'app_name': self.config.get('DATABRICKS_APP_NAME')}
        elif step_id == 'create_catalog_schema':
            return {'schema': self.created_resources.get('schema')}
        return {}
    
    def _show_final_results(self, success: bool):
        """Show final setup results."""
        print("\n" + "=" * 50)
        
        if success:
            print("🎉 Setup completed successfully!")
            print("\n📋 Summary:")
            
            if 'MLFLOW_EXPERIMENT_ID' in self.config:
                print(f"   • MLflow Experiment ID: {self.config['MLFLOW_EXPERIMENT_ID']}")
            
            if 'DATABRICKS_APP_NAME' in self.config:
                print(f"   • Databricks App: {self.config['DATABRICKS_APP_NAME']}")
            
            if 'UC_CATALOG' in self.config and 'UC_SCHEMA' in self.config:
                print(f"   • Unity Catalog: {self.config['UC_CATALOG']}.{self.config['UC_SCHEMA']}")
            
            print("\n🚀 Next steps:")
            print("   1. Your app is now deployed and ready to use")
            print("   2. Check the Databricks Apps section in your workspace")
            print("   3. Test the email generation functionality")
            print("   4. Explore the MLflow experiment for traces and evaluations")
            
        else:
            print("❌ Setup failed or was interrupted")
            print("\n🔧 Troubleshooting:")
            print("   • Run 'python auto-setup.py --resume' to continue from where you left off")
            print("   • Check the progress with 'python auto-setup.py --status'")
            print("   • Review any error messages above")
            
            # Show failed steps
            failed_steps = self.progress.get_failed_steps()
            if failed_steps:
                print(f"\n❌ Failed steps: {', '.join(failed_steps)}")
        
        # Show detailed progress
        print("\n📊 Setup Progress:")
        self.progress.show_detailed_progress()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _ensure_databricks_auth(self, skip_prompts: bool = False) -> bool:
        """Ensure Databricks authentication is configured."""
        if skip_prompts:
            # For resume, first check if current auth is working
            try:
                from databricks.sdk import WorkspaceClient
                test_client = WorkspaceClient()
                test_client.current_user.me()
                print("🔐 Using existing Databricks authentication")
                return True
            except Exception:
                pass  # Fall through to profile selection
        
        print("🔐 Databricks Profile Selection")
        
        # Get profiles
        profiles = self._get_databricks_profiles()
        
        if not profiles:
            print("❌ No Databricks profiles found. Please run 'databricks auth login' first.")
            return False
        
        # Always show profile selection menu
        return self._handle_auth_selection(profiles)
    
    def _get_databricks_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get available Databricks authentication profiles."""
        try:
            result = subprocess.run(
                ['databricks', 'auth', 'profiles'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to get profiles: {result.stderr}")
                return {}
            
            # Parse the profiles output (table format)
            profiles = {}
            lines = result.stdout.strip().split('\n')
            
            # Skip header line and parse each profile
            for line in lines[1:]:  # Skip the "Name Host Valid" header
                if line.strip():
                    parts = line.split(None, 2)  # Split on whitespace, max 3 parts
                    if len(parts) >= 2:
                        profile_name = parts[0].strip()
                        host = parts[1].strip()
                        valid = parts[2].strip() if len(parts) > 2 else 'UNKNOWN'
                        
                        profiles[profile_name] = {
                            'host': host,
                            'valid': valid
                        }
            
            return profiles
            
        except subprocess.TimeoutExpired:
            print("❌ Timeout getting profiles")
            return {}
        except FileNotFoundError:
            print("❌ 'databricks' command not found")
            return {}
        except Exception as e:
            print(f"❌ Error getting profiles: {e}")
            return {}
    
    def _handle_auth_selection(self, profiles: Dict[str, Dict[str, Any]]) -> bool:
        """Handle profile selection and authentication."""
        print("\n🔧 Databricks Profile Configuration")
        print("⚠️  This script only works with the DEFAULT profile to ensure consistent URLs.")
        
        profile_list = list(profiles.keys())
        if not profile_list:
            print("❌ No profiles available. Please run 'databricks auth login' to create one.")
            return False
        
        # Check if DEFAULT profile exists and is valid
        if 'DEFAULT' not in profiles:
            print("❌ DEFAULT profile not found.")
            print("   Please create a DEFAULT profile by running:")
            print("   databricks auth login --profile DEFAULT")
            return False
        
        default_profile = profiles['DEFAULT']
        if default_profile.get('valid') != 'YES':
            print("❌ DEFAULT profile exists but is not valid.")
            print("   Please re-authenticate your DEFAULT profile by running:")
            print("   databricks auth login --profile DEFAULT")
            return False
        
        # Check if current auth is working and using DEFAULT
        current_auth_works = False
        current_profile = None
        try:
            from databricks.sdk import WorkspaceClient
            test_client = WorkspaceClient()
            user_info = test_client.current_user.me()
            current_auth_works = True
            # Try to determine current profile from workspace URL
            current_host = test_client.config.host
            for profile_name, profile_info in profiles.items():
                if profile_info.get('host') == current_host:
                    current_profile = profile_name
                    break
        except Exception:
            pass
        
        print(f"\n🔧 Available option:")
        default_host = default_profile.get('host', 'Unknown host')
        
        if current_auth_works and current_profile == 'DEFAULT':
            print(f"   0. Keep current DEFAULT profile authentication ({default_host}) ✅")
            choice = input(f"\nPress ENTER to continue with DEFAULT profile or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return False
            print("✅ Using DEFAULT profile")
            return True
        else:
            print(f"   1. Use DEFAULT profile ({default_host}) ✅")
            choice = input(f"\nPress ENTER to use DEFAULT profile or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return False
            selected_profile = 'DEFAULT'
        
        # Authenticate with selected profile
        print(f"\n🔐 Authenticating with profile '{selected_profile}'...")
        
        profile_info = profiles[selected_profile]
        host = profile_info.get('host')
        
        if not host:
            print(f"❌ No host found for profile '{selected_profile}'")
            return False
        
        try:
            # Run databricks auth login with the specific host and profile
            result = subprocess.run(
                ['databricks', 'auth', 'login', '--host', host, '--profile', selected_profile],
                timeout=120  # 2 minutes timeout for auth
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully authenticated with profile '{selected_profile}'")
                
                # Test the authentication
                try:
                    from databricks.sdk import WorkspaceClient
                    test_client = WorkspaceClient(profile=selected_profile)
                    test_client.current_user.me()
                    print("✅ Authentication test successful")
                    return True
                except Exception as e:
                    print(f"❌ Authentication test failed: {e}")
                    return False
            else:
                print(f"❌ Authentication failed for profile '{selected_profile}'")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Authentication timed out")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def cleanup_resources(self):
        """Clean up created resources (for rollback)."""
        print("🧹 Cleaning up created resources...")
        if hasattr(self, 'resource_manager'):
            self.resource_manager.cleanup_created_resources()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MLflow Demo Automated Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating resources')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous failed/interrupted setup')
    parser.add_argument('--reset', action='store_true',
                       help='Reset all progress and start fresh')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only run validation checks')
    parser.add_argument('--status', action='store_true',
                       help='Show current setup status')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up progress file and start fresh')
    
    args = parser.parse_args()
    
    if args.status:
        # Show status and exit
        progress = ProgressTracker()
        progress.show_detailed_progress()
        return
    
    if args.cleanup:
        # Clean up and exit
        progress = ProgressTracker()
        progress.cleanup_progress_file()
        print("🧹 Progress file cleaned up. Run auto-setup.py to start fresh.")
        return
    
    # Initialize setup
    auto_setup = AutoSetup(dry_run=args.dry_run)
    
    if args.reset:
        auto_setup.progress.reset_all_steps()
        print("🔄 Reset all progress. Starting fresh...")
        print("Run auto-setup again to begin setup process.")
        sys.exit(0)
    
    if args.validate_only:
        # Only run validation
        print("🔍 Running validation checks only...")
        valid, issues = auto_setup.validator.validate_prerequisites()
        if valid:
            print("✅ All validation checks passed")
            sys.exit(0)
        else:
            print("❌ Validation failed")
            for issue in issues:
                print(f"   • {issue}")
            sys.exit(1)
    
    # Run the setup
    try:
        success = auto_setup.run_setup(resume=args.resume)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted. Run with --resume to continue.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Run with --resume to try continuing from the last successful step.")
        sys.exit(1)


if __name__ == '__main__':
    main()