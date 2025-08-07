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
    
    def create_databricks_app(self, name: str, description: str = None, source_code_path: str = None) -> App:
        """Create a Databricks App.
        
        Args:
            name: Name of the app
            description: Optional description
            source_code_path: Workspace path for the app source code
            
        Returns:
            App object
        """
        try:
            print(f"📱 Creating Databricks App '{name}'...")
            
            # Check if app already exists first
            try:
                existing_app = self.client.apps.get(name)
                print(f"✅ App '{name}' already exists")
                self.created_resources.append(('app', name))
                return existing_app
            except NotFound:
                pass  # App doesn't exist, we'll create it
            
            # Create the Databricks App
            try:
                # Import the App class from the SDK
                from databricks.sdk.service.apps import App
                
                app_source_path = source_code_path or f"/Workspace/Shared/{name}"
                
                # Create the App object with proper structure
                app_config = App(
                    name=name,
                    description=description or f"MLflow demo application - {name}",
                    default_source_code_path=app_source_path
                )
                
                # Create the app using the correct SDK method signature
                app_waiter = self.client.apps.create(
                    app=app_config,
                    no_compute=True  # Don't start the app immediately
                )
                
                # Wait for the creation to complete - app may be in STOPPED state which is expected
                try:
                    app = app_waiter.result()
                except Exception as waiter_error:
                    # If waiter fails due to STOPPED state, try to get the app directly
                    if "STOPPED" in str(waiter_error):
                        print(f"📱 App created but in STOPPED state (expected with no_compute=True)")
                        app = self.client.apps.get(name)
                    else:
                        raise waiter_error
                
                print(f"✅ Created Databricks App '{name}'")
                self.created_resources.append(('app', name))
                return app
                
            except Exception as create_error:
                print(f"⚠️  Could not create app via SDK: {create_error}")
                print(f"💡 App '{name}' will be created during deployment step")
                self.created_resources.append(('app', name))
                
                # Return a dummy app object as fallback
                class DummyApp:
                    def __init__(self, name):
                        self.name = name
                return DummyApp(name)
                
        except Exception as e:
            print(f"❌ Failed to create or check app '{name}': {e}")
            raise
    
    def start_app(self, app_name: str, timeout_minutes: int = 20) -> bool:
        """Start a Databricks App and wait for it to be active.
        
        Args:
            app_name: Name of the app to start
            timeout_minutes: Maximum time to wait for app to become active
            
        Returns:
            True if app started successfully, False otherwise
        """
        try:
            print(f"🚀 Starting Databricks App '{app_name}'...")
            
            # Start the app using the SDK's start_and_wait method
            from datetime import timedelta
            
            try:
                app = self.client.apps.start_and_wait(
                    name=app_name,
                    timeout=timedelta(minutes=timeout_minutes)
                )
                print(f"✅ App '{app_name}' started successfully and is now active")
                return True
                
            except Exception as start_error:
                print(f"⚠️  start_and_wait failed: {start_error}")
                print(f"🔄 Trying alternative approach: start + wait...")
                
                # Fallback: use start() then wait separately
                try:
                    start_waiter = self.client.apps.start(app_name)
                    start_waiter.result(timeout=timedelta(minutes=timeout_minutes))
                    
                    # Wait for app to become active
                    app = self.client.apps.wait_get_app_active(
                        name=app_name,
                        timeout=timedelta(minutes=timeout_minutes)
                    )
                    print(f"✅ App '{app_name}' started successfully and is now active")
                    return True
                    
                except Exception as fallback_error:
                    print(f"❌ Failed to start app '{app_name}': {fallback_error}")
                    print(f"💡 You may need to start the app manually from the Databricks UI")
                    return False
                
        except Exception as e:
            print(f"❌ Error starting app '{app_name}': {e}")
            return False
    
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
            
            # Use a simpler approach for granting permissions
            for permission in permissions:
                try:
                    # Try using the grants API directly with proper parameters
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
                except Exception as direct_error:
                    print(f"⚠️  Direct grants API failed: {direct_error}")
                    # Try using the SDK objects with correct constructor
                    try:
                        from databricks.sdk.service.catalog import PermissionsChange, Privilege
                        
                        # The Privilege class likely expects different parameters
                        privilege = Privilege(
                            principal=principal,
                            privileges=[permission]
                        )
                        
                        permission_change = PermissionsChange(add=[privilege])
                        
                        self.client.grants.update(
                            securable_type="schema",
                            full_name=schema_full_name,
                            changes=[permission_change]
                        )
                    except Exception as sdk_error:
                        print(f"⚠️  SDK approach also failed: {sdk_error}")
                        raise sdk_error
            print(f"✅ Granted {permissions} on '{schema_full_name}' to '{principal}'")
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant permissions on schema: {e}")
            print("You may need to grant permissions manually via the UI")
            print(f"📋 Manual steps:")
            print(f"   1. Go to your Unity Catalog schema → {schema_full_name} → Permissions tab")
            print(f"   2. Grant {permissions} to service principal: {principal}")
            print("\n⏸️  Please complete the manual permission setup, then press Enter to continue...")
            input()
    
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
                # MLflow experiment permissions are complex and often require manual setup
                # Skip automatic grants for experiments
                print(f"⚠️  Automatic experiment permissions not supported, requiring manual setup")
                
                # Construct the direct URL to the experiment
                workspace_host = self.client.config.host.rstrip('/')
                experiment_url = f"{workspace_host}/ml/experiments/{experiment_id}"
                
                print(f"📋 Manual steps:")
                print(f"   1. Open this URL: {experiment_url}")
                print(f"   2. Click on the 'Permissions' tab")
                print(f"   3. Grant {permission} permission to service principal: {principal}")
                print("\n⏸️  Please complete the manual permission setup, then press Enter to continue...")
                input()
                    
            print(f"✅ Attempted to grant {permissions} on experiment '{experiment_id}' to '{principal}'")
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant experiment permissions: {e}")
            print(f"📋 Manual steps:")
            print(f"   1. Go to your MLflow experiment → {experiment_id} → Permissions tab")
            print(f"   2. Grant {permissions} to service principal: {principal}")
            print("\n⏸️  Please complete the manual permission setup, then press Enter to continue...")
            input()
    
    def grant_model_serving_permissions(self, app_name: str, endpoint_name: str) -> None:
        """Grant model serving endpoint access to a Databricks App.
        
        Args:
            app_name: Name of the Databricks app
            endpoint_name: Name of the model serving endpoint
        """
        try:
            print(f"🔐 Granting model serving access to '{endpoint_name}' for app '{app_name}'...")
            
            # Get the app's service principal
            app_sp = self._get_app_service_principal(app_name)
            if not app_sp:
                print(f"❌ Could not find service principal for app '{app_name}'")
                raise Exception(f"App service principal not found")
            
            # Grant serving endpoint permissions to the app's service principal
            try:
                # Use the serving endpoint permissions API
                self.client.serving_endpoints.update_permissions(
                    serving_endpoint_id=endpoint_name,
                    access_control_list=[{
                        "principal": app_sp,
                        "permission_level": "CAN_QUERY"
                    }]
                )
                print(f"✅ Granted CAN_QUERY permission on serving endpoint '{endpoint_name}' to '{app_sp}'")
                
            except Exception as serving_error:
                print(f"⚠️  Could not grant serving endpoint permissions via SDK: {serving_error}")
                
                print(f"📋 Manual steps:")
                print(f"   1. Go to Databricks Apps → {app_name} → Edit")
                print(f"   2. Click Next → Add Resource → Serving Endpoint")
                print(f"   3. Select '{endpoint_name}' → Save")
                print("\n⏸️  Please complete the manual serving endpoint setup, then press Enter to continue...")
                input()
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant model serving permissions: {e}")
            print(f"📋 Manual steps:")
            print(f"   1. Go to Databricks Apps → {app_name} → Edit")
            print(f"   2. Click Next → Add Resource → Serving Endpoint")
            print(f"   3. Select '{endpoint_name}' → Save")
            print("\n⏸️  Please complete the manual serving endpoint setup, then press Enter to continue...")
            input()
    
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