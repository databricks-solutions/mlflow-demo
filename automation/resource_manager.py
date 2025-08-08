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
    
    def grant_catalog_permissions(self, catalog_name: str, principal: str, 
                                 permissions: List[str] = None) -> None:
        """Grant permissions on a catalog to a principal using SQL GRANT statements.
        
        Args:
            catalog_name: Name of the catalog
            principal: Principal to grant permissions to (e.g., service principal)
            permissions: List of permissions to grant
        """
        if permissions is None:
            permissions = ["USE CATALOG"]
        
        try:
            print(f"🔐 Granting catalog permissions on '{catalog_name}' to '{principal}'...")
            
            # Use SQL GRANT statements as the SDK grants.update doesn't support CATALOG securable type
            success_count = 0
            
            # First, try to get a warehouse_id
            warehouse_id = None
            try:
                warehouses = self.client.warehouses.list()
                if warehouses:
                    # Use the first available warehouse
                    warehouse_id = warehouses[0].id
                    print(f"   Using warehouse: {warehouse_id}")
            except Exception as e:
                print(f"   ⚠️  Could not find warehouse, trying without: {e}")
            
            for permission in permissions:
                try:
                    # CRITICAL: Get application_id for the service principal (like experiments API)
                    # SQL GRANT also needs application_id, not display name
                    application_id = None
                    try:
                        sps = self.client.service_principals.list()
                        for sp in sps:
                            if sp.display_name == principal:
                                application_id = sp.application_id
                                print(f"   Found service principal application_id: {application_id}")
                                break
                        
                        if not application_id:
                            raise Exception(f"Could not find application_id for service principal: {principal}")
                            
                    except Exception as e:
                        print(f"   ⚠️  Could not get service principal application_id: {e}")
                        # Fallback to original principal name
                        application_id = principal
                    
                    # Construct SQL GRANT statement
                    # Note: Service principal names with spaces need to be quoted
                    quoted_principal = f"`{application_id}`"
                    sql_statement = f"GRANT {permission} ON CATALOG {catalog_name} TO {quoted_principal}"
                    
                    print(f"   Executing: {sql_statement}")
                    
                    # Execute the SQL statement
                    self.client.statement_execution.execute_statement(
                        warehouse_id=warehouse_id,
                        statement=sql_statement
                    )
                    
                    success_count += 1
                    print(f"   ✅ Granted {permission}")
                    
                except Exception as sql_error:
                    print(f"   ⚠️  Failed to grant {permission}: {sql_error}")
                    continue
            
            if success_count > 0:
                print(f"✅ Successfully granted {success_count}/{len(permissions)} catalog permissions on '{catalog_name}' to '{principal}'")
            else:
                raise Exception("No catalog permissions were successfully granted")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant catalog permissions: {e}")
            print("You may need to grant catalog permissions manually via the UI")
            print(f"📋 Manual steps:")
            print(f"   1. Go to your Unity Catalog → {catalog_name} → Permissions tab")
            print(f"   2. Grant {permissions} to service principal: {principal}")
            print("\n⏸️  Please complete the manual permission setup, then press Enter to continue...")
            input()

    def grant_schema_permissions(self, schema_full_name: str, principal: str, 
                                permissions: List[str] = None) -> None:
        """Grant permissions on a schema to a principal using SQL GRANT statements.
        
        Args:
            schema_full_name: Full schema name (catalog.schema)
            principal: Principal to grant permissions to (e.g., service principal)
            permissions: List of permissions to grant
        """
        if permissions is None:
            permissions = ["ALL_PRIVILEGES", "MANAGE"]
        
        try:
            print(f"🔐 Granting permissions on schema '{schema_full_name}' to '{principal}'...")
            
            # Use SQL GRANT statements as the SDK grants.update doesn't support SCHEMA securable type
            success_count = 0
            
            # First, try to get a warehouse_id
            warehouse_id = None
            try:
                warehouses = self.client.warehouses.list()
                if warehouses:
                    # Use the first available warehouse
                    warehouse_id = warehouses[0].id
                    print(f"   Using warehouse: {warehouse_id}")
            except Exception as e:
                print(f"   ⚠️  Could not find warehouse, trying without: {e}")
            
            for permission in permissions:
                try:
                    # CRITICAL: Get application_id for the service principal (like experiments API)
                    # SQL GRANT also needs application_id, not display name
                    application_id = None
                    try:
                        sps = self.client.service_principals.list()
                        for sp in sps:
                            if sp.display_name == principal:
                                application_id = sp.application_id
                                print(f"   Found service principal application_id: {application_id}")
                                break
                        
                        if not application_id:
                            raise Exception(f"Could not find application_id for service principal: {principal}")
                            
                    except Exception as e:
                        print(f"   ⚠️  Could not get service principal application_id: {e}")
                        # Fallback to original principal name
                        application_id = principal
                    
                    # Construct SQL GRANT statement
                    # Note: Service principal names with spaces need to be quoted
                    quoted_principal = f"`{application_id}`"
                    sql_statement = f"GRANT {permission} ON SCHEMA {schema_full_name} TO {quoted_principal}"
                    
                    print(f"   Executing: {sql_statement}")
                    
                    # Execute the SQL statement
                    self.client.statement_execution.execute_statement(
                        warehouse_id=warehouse_id,
                        statement=sql_statement
                    )
                    
                    success_count += 1
                    print(f"   ✅ Granted {permission}")
                    
                except Exception as sql_error:
                    print(f"   ⚠️  Failed to grant {permission}: {sql_error}")
                    continue
            
            if success_count > 0:
                print(f"✅ Successfully granted {success_count}/{len(permissions)} permissions on '{schema_full_name}' to '{principal}'")
            else:
                raise Exception("No permissions were successfully granted")
                
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
            
            # Import necessary types from the SDK
            from databricks.sdk.service.ml import ExperimentAccessControlRequest, ExperimentPermissionLevel
            
            # Map permission strings to SDK enums
            permission_map = {
                "CAN_MANAGE": ExperimentPermissionLevel.CAN_MANAGE,
                "CAN_EDIT": ExperimentPermissionLevel.CAN_EDIT,
                "CAN_READ": ExperimentPermissionLevel.CAN_READ
            }
            
            # CRITICAL: Need to get the application_id from the service principal name
            # The experiments API requires application_id, not display name
            application_id = None
            try:
                sps = self.client.service_principals.list()
                for sp in sps:
                    if sp.display_name == principal:
                        application_id = sp.application_id
                        print(f"   Found service principal application_id: {application_id}")
                        break
                
                if not application_id:
                    raise Exception(f"Could not find application_id for service principal: {principal}")
                    
            except Exception as e:
                print(f"⚠️  Could not get service principal application_id: {e}")
                raise e
            
            # First, get existing permissions to preserve them
            existing_permissions = self.client.experiments.get_permissions(experiment_id=experiment_id)
            
            # Start with existing access control list
            access_control_list = []
            
            # Add existing permissions (only preserve direct grants, not inherited)
            if existing_permissions.access_control_list:
                for existing_acl in existing_permissions.access_control_list:
                    # Skip if this is the same principal we're about to add (to avoid duplicates)
                    if existing_acl.service_principal_name == application_id:
                        continue
                    
                    # Only preserve direct (non-inherited) permissions
                    direct_permissions = [p for p in existing_acl.all_permissions if not p.inherited]
                    if not direct_permissions:
                        continue
                    
                    # Convert existing permission to request format
                    permission_level = direct_permissions[0].permission_level
                    
                    if existing_acl.user_name:
                        access_control_list.append(ExperimentAccessControlRequest(
                            user_name=existing_acl.user_name,
                            permission_level=permission_level
                        ))
                    elif existing_acl.group_name:
                        access_control_list.append(ExperimentAccessControlRequest(
                            group_name=existing_acl.group_name,
                            permission_level=permission_level
                        ))
                    elif existing_acl.service_principal_name:
                        access_control_list.append(ExperimentAccessControlRequest(
                            service_principal_name=existing_acl.service_principal_name,
                            permission_level=permission_level
                        ))
            
            # Add new permissions for the specified principal using application_id
            for permission in permissions:
                if permission in permission_map:
                    # Create ExperimentAccessControlRequest for service principal using application_id
                    access_control_request = ExperimentAccessControlRequest(
                        service_principal_name=application_id,
                        permission_level=permission_map[permission]
                    )
                    access_control_list.append(access_control_request)
                else:
                    print(f"⚠️  Unknown permission: {permission}, skipping...")
                    continue
            
            if not access_control_list:
                print("⚠️  No valid permissions found, skipping permission grant")
                return
            
            # Use the experiments API to set permissions (replaces all permissions)
            result = self.client.experiments.set_permissions(
                experiment_id=experiment_id,
                access_control_list=access_control_list
            )
            
            print(f"✅ Granted {permissions} on experiment '{experiment_id}' to '{principal}' (preserved existing permissions)")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to grant experiment permissions: {e}")
            
            # Fallback to manual instructions
            workspace_host = self.client.config.host.rstrip('/')
            experiment_url = f"{workspace_host}/ml/experiments/{experiment_id}"
            
            print(f"📋 Manual steps:")
            print(f"   1. Open this URL: {experiment_url}")
            print(f"   2. Click on the 'Permissions' tab")
            print(f"   3. Grant {permissions} to service principal: {principal}")
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
            
            # Get the app's service principal details
            app_sp_display_name = self.get_app_service_principal(app_name)
            if not app_sp_display_name:
                print(f"❌ Could not find service principal for app '{app_name}'")
                raise Exception(f"App service principal not found")
            
            # Get the service principal application_id (consistent with other APIs)
            application_id = None
            try:
                sps = self.client.service_principals.list()
                for sp in sps:
                    if sp.display_name == app_sp_display_name:
                        application_id = sp.application_id
                        print(f"   Found service principal application_id: {application_id}")
                        break
                
                if not application_id:
                    raise Exception(f"Could not find application_id for service principal: {app_sp_display_name}")
                    
            except Exception as e:
                print(f"⚠️  Could not get service principal application_id: {e}")
                raise e
            
            # Check if this is a Foundation Model endpoint (which may not support permissions)
            if any(fm_name in endpoint_name.lower() for fm_name in ['databricks-']):
                print(f"⚠️  '{endpoint_name}' appears to be a Foundation Model endpoint")
                print(f"   Foundation Model endpoints typically don't require explicit permissions")
                print(f"   The app should have access by default if it has proper workspace permissions")
                print(f"✅ Skipping explicit permission grant for Foundation Model endpoint")
                return
            
            # Try to grant permissions to custom serving endpoints
            try:
                # Import proper serving endpoint permission classes
                from databricks.sdk.service.serving import ServingEndpointAccessControlRequest, ServingEndpointPermissionLevel
                
                # Create access control request using application_id
                access_control_request = ServingEndpointAccessControlRequest(
                    service_principal_name=application_id,
                    permission_level=ServingEndpointPermissionLevel.CAN_QUERY
                )
                
                # Use the serving endpoint permissions API
                result = self.client.serving_endpoints.update_permissions(
                    serving_endpoint_id=endpoint_name,
                    access_control_list=[access_control_request]
                )
                print(f"✅ Granted CAN_QUERY permission on serving endpoint '{endpoint_name}' to '{app_sp_display_name}'")
                
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