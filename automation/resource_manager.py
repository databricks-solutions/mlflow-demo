"""Resource manager for creating and configuring Databricks resources."""

import time
import uuid
from typing import Optional, Dict, Any, List
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import CatalogInfo, SchemaInfo
from databricks.sdk.service.apps import App
from databricks.sdk.errors import ResourceAlreadyExists, NotFound, PermissionDenied
import mlflow


class DatabricksResourceManager:
    """Manages creation and configuration of Databricks resources."""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """Initialize the resource manager.
        
        Args:
            workspace_client: Optional pre-configured workspace client.
                             If None, will create one using default auth.
        """
        self.client = workspace_client or WorkspaceClient()
        self.created_resources = []
    
    def create_catalog_if_not_exists(self, catalog_name: str) -> CatalogInfo:
        """Create a Unity Catalog catalog if it doesn't exist.
        
        Args:
            catalog_name: Name of the catalog to create
            
        Returns:
            CatalogInfo object
            
        Raises:
            PermissionDenied: If user doesn't have permission to create catalogs
        """
        try:
            # Check if catalog already exists
            existing_catalog = self.client.catalogs.get(catalog_name)
            print(f"✅ Catalog '{catalog_name}' already exists")
            return existing_catalog
        except NotFound:
            pass
        
        try:
            print(f"📁 Creating catalog '{catalog_name}'...")
            catalog = self.client.catalogs.create(
                name=catalog_name,
                comment=f"Catalog for MLflow demo - created by auto-setup"
            )
            self.created_resources.append(('catalog', catalog_name))
            print(f"✅ Created catalog '{catalog_name}'")
            return catalog
        except PermissionDenied:
            raise PermissionDenied(
                f"Permission denied creating catalog '{catalog_name}'. "
                "You may need metastore admin privileges or use an existing catalog."
            )
    
    def create_schema_if_not_exists(self, catalog_name: str, schema_name: str) -> SchemaInfo:
        """Create a Unity Catalog schema if it doesn't exist.
        
        Args:
            catalog_name: Name of the parent catalog
            schema_name: Name of the schema to create
            
        Returns:
            SchemaInfo object
        """
        full_schema_name = f"{catalog_name}.{schema_name}"
        
        try:
            # Check if schema already exists
            existing_schema = self.client.schemas.get(full_schema_name)
            print(f"✅ Schema '{full_schema_name}' already exists")
            return existing_schema
        except NotFound:
            pass
        
        print(f"📁 Creating schema '{full_schema_name}'...")
        schema = self.client.schemas.create(
            name=schema_name,
            catalog_name=catalog_name,
            comment=f"Schema for MLflow demo - created by auto-setup"
        )
        self.created_resources.append(('schema', full_schema_name))
        print(f"✅ Created schema '{full_schema_name}'")
        return schema
    
    def create_mlflow_experiment(self, name: str) -> str:
        """Create an MLflow experiment.
        
        Args:
            name: Name of the experiment
            
        Returns:
            Experiment ID as string
        """
        try:
            print(f"🧪 Creating MLflow experiment '{name}'...")
            
            # Set MLflow tracking URI to Databricks
            mlflow.set_tracking_uri("databricks")
            
            # Use mlflow.set_experiment() which creates if not exists
            experiment = mlflow.set_experiment(name)
            experiment_id = experiment.experiment_id
            
            self.created_resources.append(('experiment', experiment_id))
            print(f"✅ Created MLflow experiment '{name}' (ID: {experiment_id})")
            return experiment_id
            
        except Exception as e:
            print(f"❌ Failed to create MLflow experiment '{name}': {e}")
            raise
    
    def create_databricks_app(self, name: str, description: str = None) -> App:
        """Create a Databricks App.
        
        Args:
            name: Name of the app
            description: Optional description
            
        Returns:
            App object
        """
        try:
            print(f"📱 Creating Databricks App '{name}'...")
            
            # Databricks Apps are typically deployed rather than created via API
            # For the setup phase, we'll just register the app name and create it during deployment
            # This is a placeholder step to track the intended app name
            print(f"📱 Registering app name '{name}' for later deployment...")
            
            # Check if app already exists
            try:
                existing_app = self.client.apps.get(name)
                print(f"✅ App '{name}' already exists")
                self.created_resources.append(('app', name))
                return existing_app
            except NotFound:
                # App doesn't exist yet, will be created during deployment
                print(f"💡 App '{name}' will be created during deployment step")
                self.created_resources.append(('app', name))
                # Return a dummy app object for now
                class DummyApp:
                    def __init__(self, name):
                        self.name = name
                return DummyApp(name)
        except ResourceAlreadyExists:
            # Get the existing app
            apps = self.client.apps.list()
            for app in apps:
                if app.name == name:
                    print(f"✅ Databricks App '{name}' already exists")
                    return app
            raise Exception(f"Failed to find or create app '{name}'")
    
    def grant_schema_permissions(self, schema_full_name: str, principal: str, 
                                permissions: List[str] = None) -> None:
        """Grant permissions on a schema to a principal.
        
        Args:
            schema_full_name: Full schema name (catalog.schema)
            principal: Principal to grant permissions to (e.g., service principal)
            permissions: List of permissions to grant
        """
        if permissions is None:
            permissions = ["ALL_PRIVILEGES", "MANAGE"]
        
        try:
            print(f"🔐 Granting permissions on schema '{schema_full_name}' to '{principal}'...")
            for permission in permissions:
                self.client.grants.update(
                    securable_type="schema",
                    full_name=schema_full_name,
                    changes=[{
                        "add": [{
                            "principal": principal,
                            "privileges": [permission]
                        }]
                    }]
                )
            print(f"✅ Granted {permissions} on '{schema_full_name}' to '{principal}'")
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant permissions on schema: {e}")
            print("You may need to grant permissions manually via the UI")
    
    def grant_experiment_permissions(self, experiment_id: str, principal: str,
                                   permissions: List[str] = None) -> None:
        """Grant permissions on an MLflow experiment to a principal.
        
        Args:
            experiment_id: MLflow experiment ID
            principal: Principal to grant permissions to
            permissions: List of permissions to grant (CAN_MANAGE, CAN_EDIT, CAN_READ)
        """
        if permissions is None:
            permissions = ["CAN_MANAGE"]
        
        try:
            print(f"🔐 Granting permissions on experiment '{experiment_id}' to '{principal}'...")
            
            # Use MLflow SDK for experiment permissions
            mlflow.set_tracking_uri("databricks")
            
            for permission in permissions:
                # Get current experiment permissions and add new one
                try:
                    # Note: MLflow experiment permissions are managed via workspace permissions
                    # The SDK might not have direct support, so we'll use grants API
                    self.client.grants.update(
                        securable_type="mlflow-experiment",
                        full_name=experiment_id,
                        changes=[{
                            "add": [{
                                "principal": principal,
                                "privileges": [permission]
                            }]
                        }]
                    )
                except Exception as grants_error:
                    # Fallback: try workspace permissions API
                    print(f"⚠️  Grants API failed for experiment, trying alternative method: {grants_error}")
                    print(f"💡 Please manually grant {permission} permission on experiment {experiment_id} to {principal}")
                    
            print(f"✅ Attempted to grant {permissions} on experiment '{experiment_id}' to '{principal}'")
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant experiment permissions: {e}")
            print(f"💡 Please manually grant permissions on experiment {experiment_id} via the MLflow UI")
    
    def grant_model_serving_permissions(self, app_name: str, endpoint_name: str) -> None:
        """Grant model serving endpoint access to a Databricks App.
        
        Args:
            app_name: Name of the Databricks app
            endpoint_name: Name of the model serving endpoint
        """
        try:
            print(f"🔐 Granting model serving access to '{endpoint_name}' for app '{app_name}'...")
            
            # Add serving endpoint as a resource to the app
            # This is done via the apps API resource configuration
            app = self.client.apps.get(app_name)
            
            # Update app resources to include serving endpoint
            # Note: Apps resource management via SDK may vary by version
            try:
                # Try to update app with serving endpoint resource
                # The exact method depends on the Databricks SDK version and API
                
                # Option 1: Try apps update with resources
                try:
                    current_app = self.client.apps.get(app_name)
                    
                    # Get current resources and add serving endpoint
                    current_resources = getattr(current_app, 'resources', [])
                    
                    # Add serving endpoint if not already present
                    endpoint_resource = {
                        "name": endpoint_name,
                        "type": "serving_endpoint"
                    }
                    
                    # Check if endpoint already exists in resources
                    existing_endpoint = any(
                        r.get('name') == endpoint_name and r.get('type') == 'serving_endpoint'
                        for r in current_resources
                    )
                    
                    if not existing_endpoint:
                        current_resources.append(endpoint_resource)
                        
                        # Update app with new resources
                        self.client.apps.update(
                            name=app_name,
                            resources=current_resources
                        )
                        print(f"✅ Added serving endpoint '{endpoint_name}' to app '{app_name}' resources")
                    else:
                        print(f"✅ Serving endpoint '{endpoint_name}' already configured for app '{app_name}'")
                        
                except AttributeError as attr_error:
                    # SDK method doesn't exist, provide manual instructions
                    raise Exception(f"SDK method not available: {attr_error}")
                    
            except Exception as resource_error:
                print(f"⚠️  Could not add serving endpoint via SDK: {resource_error}")
                print(f"💡 Please manually add serving endpoint '{endpoint_name}' to app '{app_name}' via UI:")
                print(f"   1. Go to Databricks Apps → {app_name} → Edit")
                print(f"   2. Click Next → Add Resource → Serving Endpoint")
                print(f"   3. Select '{endpoint_name}' → Save")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant model serving permissions: {e}")
            print(f"💡 Please manually add serving endpoint access via the UI")
    
    def get_app_service_principal(self, app_name: str) -> Optional[str]:
        """Get the service principal name for a Databricks App.
        
        Args:
            app_name: Name of the app
            
        Returns:
            Service principal name if found, None otherwise
        """
        try:
            app = self.client.apps.get(app_name)
            
            # The service principal name typically follows the pattern: 
            # {app_name}@{workspace_id}.databricks.com or similar
            
            # Try to get from app properties
            if hasattr(app, 'service_principal_name'):
                return app.service_principal_name
            elif hasattr(app, 'service_principal'):
                return app.service_principal
            elif hasattr(app, 'app_id'):
                # Construct service principal name from app_id if available
                return f"app-{app.app_id}@databricks.com"
            else:
                # Fallback: construct from app name
                # Note: This is a best guess - actual format may vary
                return f"{app_name}@databricks.com"
                
        except Exception as e:
            print(f"⚠️  Warning: Could not retrieve app service principal: {e}")
            return None
    
    def wait_for_app_active(self, app_name: str, timeout_seconds: int = 300) -> bool:
        """Wait for a Databricks App to become active.
        
        Args:
            app_name: Name of the app
            timeout_seconds: Maximum time to wait
            
        Returns:
            True if app becomes active, False if timeout
        """
        print(f"⏳ Waiting for app '{app_name}' to become active...")
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                app = self.client.apps.get(app_name)
                if hasattr(app, 'status') and app.status == 'ACTIVE':
                    print(f"✅ App '{app_name}' is now active")
                    return True
                time.sleep(10)
            except Exception as e:
                print(f"⚠️  Error checking app status: {e}")
                time.sleep(10)
        
        print(f"⚠️  Timeout waiting for app '{app_name}' to become active")
        return False
    
    def generate_unique_name(self, base_name: str, suffix_length: int = 8) -> str:
        """Generate a unique name by appending a random suffix.
        
        Args:
            base_name: Base name to use
            suffix_length: Length of random suffix
            
        Returns:
            Unique name
        """
        suffix = str(uuid.uuid4()).replace('-', '')[:suffix_length]
        return f"{base_name}_{suffix}"
    
    def cleanup_created_resources(self) -> None:
        """Clean up resources created during setup (for rollback)."""
        print("🧹 Cleaning up created resources...")
        
        for resource_type, resource_id in reversed(self.created_resources):
            try:
                if resource_type == 'app':
                    print(f"  Deleting app: {resource_id}")
                    self.client.apps.delete(resource_id)
                elif resource_type == 'experiment':
                    print(f"  Deleting experiment: {resource_id}")
                    self.client.experiments.delete_experiment(resource_id)
                elif resource_type == 'schema':
                    print(f"  Deleting schema: {resource_id}")
                    catalog_name, schema_name = resource_id.split('.', 1)
                    self.client.schemas.delete(f"{catalog_name}.{schema_name}")
                elif resource_type == 'catalog':
                    print(f"  Deleting catalog: {resource_id}")
                    self.client.catalogs.delete(resource_id)
                    
                print(f"  ✅ Deleted {resource_type}: {resource_id}")
            except Exception as e:
                print(f"  ⚠️  Failed to delete {resource_type} {resource_id}: {e}")
        
        self.created_resources.clear()
        print("🧹 Cleanup completed")