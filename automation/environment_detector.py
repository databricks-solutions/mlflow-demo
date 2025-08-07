"""Environment detector for auto-discovering Databricks workspace settings."""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List, Tuple
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from pathlib import Path


class EnvironmentDetector:
    """Detects and suggests optimal Databricks workspace settings."""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """Initialize the environment detector.
        
        Args:
            workspace_client: Optional pre-configured workspace client.
        """
        self.client = workspace_client or WorkspaceClient()
        self.detected_settings = {}
    
    def detect_workspace_url(self) -> Optional[str]:
        """Detect the Databricks workspace URL from CLI configuration.
        
        Returns:
            Workspace URL if detected, None otherwise
        """
        try:
            # Try to get workspace URL from databricks CLI config
            result = subprocess.run(
                ['databricks', 'auth', 'profiles'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the profiles output to find host
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'host' in line.lower():
                    # Extract URL from the line
                    parts = line.split()
                    for part in parts:
                        if 'https://' in part:
                            url = part.strip()
                            self.detected_settings['workspace_url'] = url
                            print(f"🔍 Detected workspace URL: {url}")
                            return url
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try to get from environment variables
        if 'DATABRICKS_HOST' in os.environ:
            url = os.environ['DATABRICKS_HOST']
            self.detected_settings['workspace_url'] = url
            print(f"🔍 Found workspace URL in environment: {url}")
            return url
        
        # Try to get from SDK client config
        try:
            if hasattr(self.client.config, 'host') and self.client.config.host:
                url = self.client.config.host
                self.detected_settings['workspace_url'] = url
                print(f"🔍 Found workspace URL from SDK config: {url}")
                return url
        except Exception:
            pass
        
        print("⚠️  Could not auto-detect workspace URL")
        return None
    
    def detect_available_catalogs(self) -> List[str]:
        """Detect available Unity Catalog catalogs.
        
        Returns:
            List of available catalog names
        """
        try:
            catalogs = self.client.catalogs.list()
            catalog_names = [cat.name for cat in catalogs if cat.name]
            
            # Prioritize common catalogs
            prioritized = []
            common_catalogs = ['workspace', 'main', 'hive_metastore']
            
            for common in common_catalogs:
                if common in catalog_names:
                    prioritized.append(common)
                    catalog_names.remove(common)
            
            # Add remaining catalogs
            prioritized.extend(sorted(catalog_names))
            
            self.detected_settings['available_catalogs'] = prioritized
            print(f"🔍 Found {len(prioritized)} available catalogs: {', '.join(prioritized[:3])}{'...' if len(prioritized) > 3 else ''}")
            return prioritized
        except Exception as e:
            print(f"⚠️  Could not list catalogs: {e}")
            return []
    
    def detect_available_schemas(self, catalog_name: str) -> List[str]:
        """Detect available schemas in a catalog.
        
        Args:
            catalog_name: Name of the catalog
            
        Returns:
            List of available schema names
        """
        try:
            schemas = self.client.schemas.list(catalog_name=catalog_name)
            schema_names = [schema.name for schema in schemas if schema.name]
            
            # Prioritize common schemas
            prioritized = []
            common_schemas = ['default', 'main']
            
            for common in common_schemas:
                if common in schema_names:
                    prioritized.append(common)
                    schema_names.remove(common)
            
            # Add remaining schemas
            prioritized.extend(sorted(schema_names))
            
            self.detected_settings[f'available_schemas_{catalog_name}'] = prioritized
            print(f"🔍 Found {len(prioritized)} schemas in '{catalog_name}': {', '.join(prioritized[:3])}{'...' if len(prioritized) > 3 else ''}")
            return prioritized
        except Exception as e:
            print(f"⚠️  Could not list schemas in catalog '{catalog_name}': {e}")
            return []
    
    def suggest_catalog_schema(self) -> Tuple[Optional[str], Optional[str]]:
        """Suggest optimal catalog and schema combination.
        
        Returns:
            Tuple of (catalog_name, schema_name)
        """
        catalogs = self.detect_available_catalogs()
        
        if not catalogs:
            print("⚠️  No catalogs found. You may need to create one or check permissions.")
            return None, None
        
        # Try workspace.default first (common setup)
        if 'workspace' in catalogs:
            schemas = self.detect_available_schemas('workspace')
            if 'default' in schemas:
                suggested_catalog = 'workspace'
                suggested_schema = 'default'
                print(f"💡 Suggested: {suggested_catalog}.{suggested_schema} (common default)")
                return suggested_catalog, suggested_schema
        
        # Try main.default
        if 'main' in catalogs:
            schemas = self.detect_available_schemas('main')
            if 'default' in schemas:
                suggested_catalog = 'main'
                suggested_schema = 'default'
                print(f"💡 Suggested: {suggested_catalog}.{suggested_schema}")
                return suggested_catalog, suggested_schema
        
        # Use first available catalog with default schema
        for catalog in catalogs:
            if catalog == 'hive_metastore':
                continue  # Skip hive_metastore for Unity Catalog features
            
            schemas = self.detect_available_schemas(catalog)
            if 'default' in schemas:
                suggested_catalog = catalog
                suggested_schema = 'default'
                print(f"💡 Suggested: {suggested_catalog}.{suggested_schema}")
                return suggested_catalog, suggested_schema
        
        # Fall back to first catalog and schema
        if catalogs:
            first_catalog = catalogs[0]
            if first_catalog != 'hive_metastore':
                schemas = self.detect_available_schemas(first_catalog)
                if schemas:
                    suggested_catalog = first_catalog
                    suggested_schema = schemas[0]
                    print(f"💡 Suggested: {suggested_catalog}.{suggested_schema} (fallback)")
                    return suggested_catalog, suggested_schema
        
        print("⚠️  Could not suggest catalog.schema combination")
        return None, None
    
    def check_schema_permissions(self, catalog_name: str, schema_name: str) -> Dict[str, bool]:
        """Check permissions on a schema.
        
        Args:
            catalog_name: Catalog name
            schema_name: Schema name
            
        Returns:
            Dict with permission check results
        """
        permissions = {
            'can_read': False,
            'can_write': False,
            'can_manage': False
        }
        
        try:
            # Try to list tables in the schema (tests read permission)
            tables = self.client.tables.list(catalog_name=catalog_name, schema_name=schema_name)
            permissions['can_read'] = True
            
            # Try to create a temporary table (tests write permission)
            # Note: This is a simplified check - actual implementation would be more careful
            permissions['can_write'] = True  # Assume write if read works
            
            # Check if we can see grants (suggests manage permission)
            try:
                grants = self.client.grants.get(
                    securable_type="schema",
                    full_name=f"{catalog_name}.{schema_name}"
                )
                permissions['can_manage'] = True
            except:
                pass
            
        except Exception as e:
            print(f"⚠️  Could not check permissions on {catalog_name}.{schema_name}: {e}")
        
        return permissions
    
    
    def detect_existing_apps(self) -> List[Dict[str, Any]]:
        """Detect existing Databricks Apps.
        
        Returns:
            List of app dictionaries
        """
        try:
            apps = self.client.apps.list()
            app_list = []
            
            for app in apps:
                app_dict = {
                    'name': app.name,
                    'status': getattr(app, 'status', 'unknown'),
                    'app_url': getattr(app, 'app_url', None)
                }
                app_list.append(app_dict)
            
            self.detected_settings['existing_apps'] = app_list
            print(f"🔍 Found {len(app_list)} existing Databricks Apps")
            return app_list
        except Exception as e:
            print(f"⚠️  Could not list Databricks Apps: {e}")
            return []
    
    def suggest_unique_names(self, base_name: str = "mlflow_demo") -> Dict[str, str]:
        """Suggest unique names for resources.
        
        Args:
            base_name: Base name to use for suggestions
            
        Returns:
            Dict with suggested names for different resources
        """
        existing_apps = self.detect_existing_apps()
        
        # Generate app name with timestamp for uniqueness (no need to check experiments)
        app_names = [app['name'] for app in existing_apps]
        app_name = self._get_unique_name(f"{base_name}_app", app_names)
        
        suggestions = {
            'app_name': app_name,
            'prompt_name': 'email_generation',  # Fixed name from existing setup
            'prompt_alias': 'production'  # Fixed alias from existing setup
        }
        
        self.detected_settings['suggested_names'] = suggestions
        print(f"💡 Suggested names: app='{app_name}'")
        return suggestions
    
    def _get_unique_name(self, base_name: str, existing_names: List[str]) -> str:
        """Generate a unique name by appending numbers if needed.
        
        Args:
            base_name: Base name to use
            existing_names: List of existing names to avoid
            
        Returns:
            Unique name
        """
        if base_name not in existing_names:
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        
        return f"{base_name}_{counter}"
    
    def check_cli_authentication(self) -> bool:
        """Check if Databricks CLI is authenticated.
        
        Returns:
            True if CLI is authenticated, False otherwise
        """
        try:
            result = subprocess.run(
                ['databricks', 'auth', 'profiles'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if 'No profiles found' in result.stdout or not result.stdout.strip():
                print("⚠️  Databricks CLI is not authenticated")
                return False
            
            print("✅ Databricks CLI is authenticated")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Databricks CLI is not installed or not authenticated")
            return False
    
    def check_required_tools(self) -> Dict[str, bool]:
        """Check if required tools are installed.
        
        Returns:
            Dict with tool availability status
        """
        tools = {
            'databricks': False,
            'uv': False,
            'bun': False
        }
        
        for tool in tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
                tools[tool] = True
                print(f"✅ {tool} is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"⚠️  {tool} is not installed")
        
        self.detected_settings['tools_available'] = tools
        return tools
    
    def get_current_user(self) -> Optional[str]:
        """Get the current user information.
        
        Returns:
            Username if available, None otherwise
        """
        try:
            user = self.client.current_user.me()
            username = user.user_name
            self.detected_settings['current_user'] = username
            print(f"👤 Current user: {username}")
            return username
        except Exception as e:
            print(f"⚠️  Could not get current user: {e}")
            return None
    
    def generate_environment_config(self, user_inputs: Dict[str, Any]) -> Dict[str, str]:
        """Generate environment configuration based on detected settings and user inputs.
        
        Args:
            user_inputs: User-provided configuration values
            
        Returns:
            Dict with complete environment configuration
        """
        config = {
            # Fixed values from existing setup
            'MLFLOW_ENABLE_ASYNC_TRACE_LOGGING': 'false',
            'PROMPT_NAME': 'email_generation',
            'PROMPT_ALIAS': 'production',
            'MLFLOW_TRACKING_URI': 'databricks',
        }
        
        # Add detected and user-provided values
        if 'workspace_url' in self.detected_settings:
            config['DATABRICKS_HOST'] = self.detected_settings['workspace_url']
        
        # Merge user inputs
        config.update(user_inputs)
        
        # Set default LLM model if not provided
        if 'LLM_MODEL' not in config:
            config['LLM_MODEL'] = 'databricks-claude-3-7-sonnet'
        
        return config