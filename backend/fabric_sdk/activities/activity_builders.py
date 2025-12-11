"""
Activity Builders for Microsoft Fabric Data Pipelines

Provides fluent builder classes for generating pipeline activity JSON definitions.
These replace the hardcoded activity generators in the original fabric_api_service.py.

Usage:
    from fabric_sdk.activities import CopyActivity, ForEachActivity, PipelineBuilder

    # Build a copy activity
    copy = CopyActivity("CopyData") \
        .from_blob(workspace_id, lakehouse_id, "source/") \
        .to_lakehouse_table(workspace_id, lakehouse_id, "target_table") \
        .depends_on("PreviousActivity") \
        .build()

    # Build a complete pipeline
    pipeline = PipelineBuilder("MyPipeline") \
        .add_activity(copy) \
        .add_variable("counter", "Int", 0) \
        .build()
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod


class ActivityBuilder(ABC):
    """
    Base class for all activity builders.

    Provides common functionality for building pipeline activities.
    """

    def __init__(self, name: str, activity_type: str):
        """
        Initialize an activity builder.

        Args:
            name: Activity name (unique within pipeline)
            activity_type: Activity type (Copy, ForEach, etc.)
        """
        self.name = name
        self.activity_type = activity_type
        self._depends_on: List[Dict[str, Any]] = []
        self._policy: Dict[str, Any] = {
            "timeout": "0.12:00:00",
            "retry": 0,
            "retryIntervalInSeconds": 30,
            "secureOutput": False,
            "secureInput": False
        }
        self._user_properties: List[Dict[str, Any]] = []
        self._external_references: Optional[Dict[str, Any]] = None

    def depends_on(
        self,
        activity_name: str,
        conditions: List[str] = None
    ) -> "ActivityBuilder":
        """
        Add a dependency on another activity.

        Args:
            activity_name: Name of the activity to depend on
            conditions: List of conditions (Succeeded, Failed, Skipped, Completed)

        Returns:
            Self for method chaining
        """
        self._depends_on.append({
            "activity": activity_name,
            "dependencyConditions": conditions or ["Succeeded"]
        })
        return self

    def with_timeout(self, timeout: str) -> "ActivityBuilder":
        """Set activity timeout (format: d.hh:mm:ss)."""
        self._policy["timeout"] = timeout
        return self

    def with_retry(self, count: int, interval_seconds: int = 30) -> "ActivityBuilder":
        """Set retry policy."""
        self._policy["retry"] = count
        self._policy["retryIntervalInSeconds"] = interval_seconds
        return self

    def with_connection(self, connection_id: str) -> "ActivityBuilder":
        """Set external connection reference."""
        self._external_references = {"connection": connection_id}
        return self

    def _base_activity(self) -> Dict[str, Any]:
        """Build the base activity structure."""
        activity = {
            "name": self.name,
            "type": self.activity_type,
            "dependsOn": self._depends_on,
            "policy": self._policy
        }
        if self._user_properties:
            activity["userProperties"] = self._user_properties
        if self._external_references:
            activity["externalReferences"] = self._external_references
        return activity

    @abstractmethod
    def build(self) -> Dict[str, Any]:
        """Build the complete activity JSON."""
        pass


# =============================================================================
# EXPRESSION HELPERS
# =============================================================================

def expr(value: str) -> Dict[str, Any]:
    """Create an expression object."""
    return {"value": value, "type": "Expression"}


def activity_output(activity_name: str, path: str = "") -> str:
    """Create activity output reference expression."""
    if path:
        return f"@activity('{activity_name}').output.{path}"
    return f"@activity('{activity_name}').output"


def variable(name: str) -> str:
    """Create variable reference expression."""
    return f"@variables('{name}')"


def parameter(name: str) -> str:
    """Create parameter reference expression."""
    return f"@pipeline().parameters.{name}"


def item() -> str:
    """Create item reference for ForEach loops."""
    return "@item()"


# =============================================================================
# COPY ACTIVITY
# =============================================================================

class CopyActivity(ActivityBuilder):
    """Builder for Copy activity."""

    def __init__(self, name: str):
        super().__init__(name, "Copy")
        self._source: Dict[str, Any] = {}
        self._sink: Dict[str, Any] = {}
        self._enable_staging: bool = False
        self._translator: Optional[Dict[str, Any]] = None

    def from_lakehouse_files(
        self,
        workspace_id: str,
        lakehouse_id: str,
        folder_path: str,
        file_pattern: str = "*",
        recursive: bool = True
    ) -> "CopyActivity":
        """Configure source as Lakehouse Files."""
        self._source = {
            "type": "BinarySource",
            "storeSettings": {
                "type": "LakehouseReadSettings",
                "recursive": recursive,
                "wildcardFolderPath": folder_path,
                "wildcardFileName": file_pattern
            }
        }
        return self

    def from_blob(
        self,
        container: str,
        folder_path: str = "",
        file_pattern: str = "*",
        recursive: bool = True
    ) -> "CopyActivity":
        """Configure source as Azure Blob Storage."""
        self._source = {
            "type": "BinarySource",
            "storeSettings": {
                "type": "AzureBlobStorageReadSettings",
                "recursive": recursive,
                "wildcardFolderPath": folder_path,
                "wildcardFileName": file_pattern,
                "container": container
            }
        }
        return self

    def from_delimited_text(
        self,
        container: str,
        folder_path: str,
        file_pattern: str = "*.csv",
        first_row_header: bool = True,
        column_delimiter: str = ","
    ) -> "CopyActivity":
        """Configure source as delimited text (CSV)."""
        self._source = {
            "type": "DelimitedTextSource",
            "storeSettings": {
                "type": "AzureBlobStorageReadSettings",
                "recursive": True,
                "wildcardFolderPath": folder_path,
                "wildcardFileName": file_pattern,
                "container": container
            },
            "formatSettings": {
                "type": "DelimitedTextReadSettings",
                "firstRowAsHeader": first_row_header,
                "columnDelimiter": column_delimiter
            }
        }
        return self

    def to_lakehouse_files(
        self,
        workspace_id: str,
        lakehouse_id: str,
        folder_path: str
    ) -> "CopyActivity":
        """Configure sink as Lakehouse Files."""
        self._sink = {
            "type": "BinarySink",
            "storeSettings": {
                "type": "LakehouseWriteSettings",
                "workspaceId": workspace_id,
                "artifactId": lakehouse_id,
                "rootFolder": "Files",
                "folderPath": folder_path
            }
        }
        return self

    def to_lakehouse_table(
        self,
        workspace_id: str,
        lakehouse_id: str,
        table_name: str,
        table_action: str = "Append"
    ) -> "CopyActivity":
        """Configure sink as Lakehouse Table."""
        self._sink = {
            "type": "LakehouseTableSink",
            "storeSettings": {
                "type": "LakehouseWriteSettings",
                "workspaceId": workspace_id,
                "artifactId": lakehouse_id
            },
            "tableActionOption": table_action,
            "tableName": table_name
        }
        return self

    def to_blob(
        self,
        container: str,
        folder_path: str
    ) -> "CopyActivity":
        """Configure sink as Azure Blob Storage."""
        self._sink = {
            "type": "BinarySink",
            "storeSettings": {
                "type": "AzureBlobStorageWriteSettings",
                "container": container,
                "folderPath": folder_path
            }
        }
        return self

    def with_staging(self, enabled: bool = True) -> "CopyActivity":
        """Enable/disable staging."""
        self._enable_staging = enabled
        return self

    def build(self) -> Dict[str, Any]:
        """Build the Copy activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "source": self._source,
            "sink": self._sink,
            "enableStaging": self._enable_staging
        }
        if self._translator:
            activity["typeProperties"]["translator"] = self._translator
        return activity


# =============================================================================
# FOREACH ACTIVITY
# =============================================================================

class ForEachActivity(ActivityBuilder):
    """Builder for ForEach activity."""

    def __init__(self, name: str):
        super().__init__(name, "ForEach")
        self._items_expression: str = ""
        self._is_sequential: bool = False
        self._batch_count: Optional[int] = None
        self._activities: List[Dict[str, Any]] = []

    def items(self, expression: str) -> "ForEachActivity":
        """
        Set items to iterate over.

        Args:
            expression: Expression for items (e.g., "@activity('GetMetadata').output.childItems")
        """
        self._items_expression = expression
        return self

    def sequential(self, is_sequential: bool = True) -> "ForEachActivity":
        """Set sequential execution."""
        self._is_sequential = is_sequential
        return self

    def batch_count(self, count: int) -> "ForEachActivity":
        """Set maximum parallel iterations."""
        self._batch_count = count
        return self

    def add_activity(self, activity: Dict[str, Any]) -> "ForEachActivity":
        """Add a nested activity."""
        self._activities.append(activity)
        return self

    def add_activities(self, activities: List[Dict[str, Any]]) -> "ForEachActivity":
        """Add multiple nested activities."""
        self._activities.extend(activities)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the ForEach activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "items": expr(self._items_expression),
            "isSequential": self._is_sequential,
            "activities": self._activities
        }
        if self._batch_count:
            activity["typeProperties"]["batchCount"] = self._batch_count
        return activity


# =============================================================================
# IF CONDITION ACTIVITY
# =============================================================================

class IfConditionActivity(ActivityBuilder):
    """Builder for IfCondition activity."""

    def __init__(self, name: str):
        super().__init__(name, "IfCondition")
        self._condition_expression: str = ""
        self._if_true_activities: List[Dict[str, Any]] = []
        self._if_false_activities: List[Dict[str, Any]] = []

    def condition(self, expression: str) -> "IfConditionActivity":
        """
        Set the condition expression.

        Args:
            expression: Boolean expression (e.g., "@equals(variables('status'), 'success')")
        """
        self._condition_expression = expression
        return self

    def if_true(self, activity: Dict[str, Any]) -> "IfConditionActivity":
        """Add activity for true branch."""
        self._if_true_activities.append(activity)
        return self

    def if_true_activities(self, activities: List[Dict[str, Any]]) -> "IfConditionActivity":
        """Add activities for true branch."""
        self._if_true_activities.extend(activities)
        return self

    def if_false(self, activity: Dict[str, Any]) -> "IfConditionActivity":
        """Add activity for false branch."""
        self._if_false_activities.append(activity)
        return self

    def if_false_activities(self, activities: List[Dict[str, Any]]) -> "IfConditionActivity":
        """Add activities for false branch."""
        self._if_false_activities.extend(activities)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the IfCondition activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "expression": expr(self._condition_expression),
            "ifTrueActivities": self._if_true_activities
        }
        if self._if_false_activities:
            activity["typeProperties"]["ifFalseActivities"] = self._if_false_activities
        return activity


# =============================================================================
# SET VARIABLE ACTIVITY
# =============================================================================

class SetVariableActivity(ActivityBuilder):
    """Builder for SetVariable activity."""

    def __init__(self, name: str):
        super().__init__(name, "SetVariable")
        self._variable_name: str = ""
        self._value: Any = None
        self._policy = {"secureOutput": False, "secureInput": False}

    def variable(self, name: str) -> "SetVariableActivity":
        """Set the variable name."""
        self._variable_name = name
        return self

    def value(self, value: Any) -> "SetVariableActivity":
        """
        Set the value (can be expression or literal).

        Args:
            value: Value to set (use expr() for expressions)
        """
        self._value = value
        return self

    def expression_value(self, expression: str) -> "SetVariableActivity":
        """Set an expression value."""
        self._value = expr(expression)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the SetVariable activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "variableName": self._variable_name,
            "value": self._value
        }
        return activity


# =============================================================================
# APPEND VARIABLE ACTIVITY
# =============================================================================

class AppendVariableActivity(ActivityBuilder):
    """Builder for AppendVariable activity."""

    def __init__(self, name: str):
        super().__init__(name, "AppendVariable")
        self._variable_name: str = ""
        self._value: Any = None
        self._policy = {"secureOutput": False, "secureInput": False}

    def variable(self, name: str) -> "AppendVariableActivity":
        """Set the variable name."""
        self._variable_name = name
        return self

    def value(self, value: Any) -> "AppendVariableActivity":
        """Set the value to append."""
        self._value = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build the AppendVariable activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "variableName": self._variable_name,
            "value": self._value
        }
        return activity


# =============================================================================
# FILTER ACTIVITY
# =============================================================================

class FilterActivity(ActivityBuilder):
    """Builder for Filter activity."""

    def __init__(self, name: str):
        super().__init__(name, "Filter")
        self._items_expression: str = ""
        self._condition_expression: str = ""

    def items(self, expression: str) -> "FilterActivity":
        """Set items to filter."""
        self._items_expression = expression
        return self

    def condition(self, expression: str) -> "FilterActivity":
        """Set filter condition."""
        self._condition_expression = expression
        return self

    def build(self) -> Dict[str, Any]:
        """Build the Filter activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "items": expr(self._items_expression),
            "condition": expr(self._condition_expression)
        }
        return activity


# =============================================================================
# GET METADATA ACTIVITY
# =============================================================================

class GetMetadataActivity(ActivityBuilder):
    """Builder for GetMetadata activity."""

    def __init__(self, name: str):
        super().__init__(name, "GetMetadata")
        self._field_list: List[str] = ["childItems"]
        self._dataset_settings: Optional[Dict[str, Any]] = None

    def fields(self, *fields: str) -> "GetMetadataActivity":
        """
        Set fields to retrieve.

        Available fields: childItems, itemName, itemType, size, lastModified,
                         exists, structure, columnCount
        """
        self._field_list = list(fields)
        return self

    def from_lakehouse_folder(
        self,
        workspace_id: str,
        lakehouse_id: str,
        folder_path: str = ""
    ) -> "GetMetadataActivity":
        """Configure to read from lakehouse folder."""
        self._dataset_settings = {
            "type": "LakehouseFolder",
            "linkedService": {
                "name": "LakehouseRef",
                "properties": {
                    "type": "Lakehouse",
                    "typeProperties": {
                        "workspaceId": workspace_id,
                        "artifactId": lakehouse_id,
                        "rootFolder": "Files"
                    }
                }
            },
            "typeProperties": {
                "folderPath": folder_path
            }
        }
        return self

    def from_blob_folder(
        self,
        container: str,
        folder_path: str = ""
    ) -> "GetMetadataActivity":
        """Configure to read from blob storage folder."""
        self._dataset_settings = {
            "type": "Binary",
            "linkedService": {
                "referenceName": "BlobStorageLinkedService",
                "type": "LinkedServiceReference"
            },
            "typeProperties": {
                "location": {
                    "type": "AzureBlobStorageLocation",
                    "container": container,
                    "folderPath": folder_path
                }
            }
        }
        return self

    def build(self) -> Dict[str, Any]:
        """Build the GetMetadata activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "fieldList": self._field_list
        }
        if self._dataset_settings:
            activity["typeProperties"]["datasetSettings"] = self._dataset_settings
        return activity


# =============================================================================
# SCRIPT ACTIVITY
# =============================================================================

class ScriptActivity(ActivityBuilder):
    """Builder for Script activity."""

    def __init__(self, name: str):
        super().__init__(name, "Script")
        self._scripts: List[Dict[str, Any]] = []
        self._database: Optional[str] = None
        self._script_timeout: str = "02:00:00"

    def sql(self, query: str, is_expression: bool = False) -> "ScriptActivity":
        """
        Add a SQL query.

        Args:
            query: SQL query string
            is_expression: Whether query is an expression
        """
        if is_expression:
            self._scripts.append({
                "type": "Query",
                "text": expr(query)
            })
        else:
            self._scripts.append({
                "type": "Query",
                "text": query
            })
        return self

    def database(self, name: str) -> "ScriptActivity":
        """Set the database name."""
        self._database = name
        return self

    def timeout(self, timeout: str) -> "ScriptActivity":
        """Set script execution timeout."""
        self._script_timeout = timeout
        return self

    def build(self) -> Dict[str, Any]:
        """Build the Script activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "scripts": self._scripts,
            "scriptBlockExecutionTimeout": self._script_timeout
        }
        if self._database:
            activity["typeProperties"]["database"] = self._database
        return activity


# =============================================================================
# NOTEBOOK ACTIVITY
# =============================================================================

class NotebookActivity(ActivityBuilder):
    """Builder for TridentNotebook (Fabric Notebook) activity."""

    def __init__(self, name: str):
        super().__init__(name, "TridentNotebook")
        self._notebook_id: str = ""
        self._workspace_id: str = ""
        self._parameters: Dict[str, Any] = {}

    def notebook(self, workspace_id: str, notebook_id: str) -> "NotebookActivity":
        """Set the notebook to execute."""
        self._workspace_id = workspace_id
        self._notebook_id = notebook_id
        return self

    def parameter(self, name: str, value: Any, param_type: str = "string") -> "NotebookActivity":
        """
        Add a parameter.

        Args:
            name: Parameter name
            value: Parameter value
            param_type: Parameter type (string, int, float, bool)
        """
        self._parameters[name] = {
            "value": value,
            "type": param_type
        }
        return self

    def parameters(self, params: Dict[str, Any]) -> "NotebookActivity":
        """Set all parameters at once."""
        for name, value in params.items():
            if isinstance(value, dict) and "value" in value:
                self._parameters[name] = value
            else:
                self._parameters[name] = {"value": value, "type": "string"}
        return self

    def build(self) -> Dict[str, Any]:
        """Build the TridentNotebook activity JSON."""
        activity = self._base_activity()
        activity["typeProperties"] = {
            "notebookId": self._notebook_id,
            "workspaceId": self._workspace_id
        }
        if self._parameters:
            activity["typeProperties"]["parameters"] = self._parameters
        return activity


# =============================================================================
# OTHER ACTIVITIES
# =============================================================================

class WaitActivity(ActivityBuilder):
    """Builder for Wait activity."""

    def __init__(self, name: str):
        super().__init__(name, "Wait")
        self._wait_time: int = 1

    def seconds(self, seconds: int) -> "WaitActivity":
        """Set wait time in seconds."""
        self._wait_time = seconds
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {"waitTimeInSeconds": self._wait_time}
        return activity


class FailActivity(ActivityBuilder):
    """Builder for Fail activity."""

    def __init__(self, name: str):
        super().__init__(name, "Fail")
        self._message: Any = "Pipeline failed"
        self._error_code: Any = "500"

    def message(self, msg: str, is_expression: bool = False) -> "FailActivity":
        self._message = expr(msg) if is_expression else msg
        return self

    def error_code(self, code: str, is_expression: bool = False) -> "FailActivity":
        self._error_code = expr(code) if is_expression else code
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "message": self._message,
            "errorCode": self._error_code
        }
        return activity


class SwitchActivity(ActivityBuilder):
    """Builder for Switch activity."""

    def __init__(self, name: str):
        super().__init__(name, "Switch")
        self._on_expression: str = ""
        self._cases: List[Dict[str, Any]] = []
        self._default_activities: List[Dict[str, Any]] = []

    def on(self, expression: str) -> "SwitchActivity":
        self._on_expression = expression
        return self

    def case(self, value: str, activities: List[Dict[str, Any]]) -> "SwitchActivity":
        self._cases.append({"value": value, "activities": activities})
        return self

    def default(self, activities: List[Dict[str, Any]]) -> "SwitchActivity":
        self._default_activities = activities
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "on": expr(self._on_expression),
            "cases": self._cases,
            "defaultActivities": self._default_activities
        }
        return activity


class UntilActivity(ActivityBuilder):
    """Builder for Until activity."""

    def __init__(self, name: str):
        super().__init__(name, "Until")
        self._expression: str = ""
        self._timeout: str = "0.12:00:00"
        self._activities: List[Dict[str, Any]] = []

    def condition(self, expression: str) -> "UntilActivity":
        self._expression = expression
        return self

    def add_activity(self, activity: Dict[str, Any]) -> "UntilActivity":
        self._activities.append(activity)
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "expression": expr(self._expression),
            "timeout": self._timeout,
            "activities": self._activities
        }
        return activity


class LookupActivity(ActivityBuilder):
    """Builder for Lookup activity."""

    def __init__(self, name: str):
        super().__init__(name, "Lookup")
        self._source: Dict[str, Any] = {}
        self._first_row_only: bool = True

    def source(self, source_config: Dict[str, Any]) -> "LookupActivity":
        self._source = source_config
        return self

    def all_rows(self) -> "LookupActivity":
        self._first_row_only = False
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "source": self._source,
            "firstRowOnly": self._first_row_only
        }
        return activity


class WebActivity(ActivityBuilder):
    """Builder for Web activity."""

    def __init__(self, name: str):
        super().__init__(name, "WebActivity")
        self._method: str = "GET"
        self._url: Any = ""
        self._headers: Dict[str, Any] = {}
        self._body: Any = None

    def get(self, url: str) -> "WebActivity":
        self._method = "GET"
        self._url = url
        return self

    def post(self, url: str, body: Any = None) -> "WebActivity":
        self._method = "POST"
        self._url = url
        self._body = body
        return self

    def header(self, name: str, value: str) -> "WebActivity":
        self._headers[name] = value
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "method": self._method,
            "url": self._url
        }
        if self._headers:
            activity["typeProperties"]["headers"] = self._headers
        if self._body:
            activity["typeProperties"]["body"] = self._body
        return activity


class ExecutePipelineActivity(ActivityBuilder):
    """Builder for ExecutePipeline activity."""

    def __init__(self, name: str):
        super().__init__(name, "ExecutePipeline")
        self._pipeline_reference: Dict[str, Any] = {}
        self._wait_on_completion: bool = True
        self._parameters: Dict[str, Any] = {}

    def pipeline(self, pipeline_name: str) -> "ExecutePipelineActivity":
        self._pipeline_reference = {
            "referenceName": pipeline_name,
            "type": "PipelineReference"
        }
        return self

    def wait(self, wait: bool = True) -> "ExecutePipelineActivity":
        self._wait_on_completion = wait
        return self

    def parameter(self, name: str, value: Any) -> "ExecutePipelineActivity":
        self._parameters[name] = value
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "pipeline": self._pipeline_reference,
            "waitOnCompletion": self._wait_on_completion
        }
        if self._parameters:
            activity["typeProperties"]["parameters"] = self._parameters
        return activity


class Office365EmailActivity(ActivityBuilder):
    """Builder for Office365Email activity."""

    def __init__(self, name: str):
        super().__init__(name, "Office365Email")
        self._to: str = ""
        self._subject: Any = ""
        self._body: Any = ""
        self._cc: Optional[str] = None
        self._bcc: Optional[str] = None

    def to(self, email: str) -> "Office365EmailActivity":
        self._to = email
        return self

    def subject(self, subject: str, is_expression: bool = False) -> "Office365EmailActivity":
        self._subject = expr(subject) if is_expression else subject
        return self

    def body(self, body: str, is_expression: bool = False) -> "Office365EmailActivity":
        self._body = expr(body) if is_expression else body
        return self

    def cc(self, email: str) -> "Office365EmailActivity":
        self._cc = email
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "to": self._to,
            "subject": self._subject,
            "body": self._body
        }
        if self._cc:
            activity["typeProperties"]["cc"] = self._cc
        if self._bcc:
            activity["typeProperties"]["bcc"] = self._bcc
        return activity


class RefreshDataflowActivity(ActivityBuilder):
    """Builder for RefreshDataflow activity."""

    def __init__(self, name: str):
        super().__init__(name, "RefreshDataflow")
        self._dataflow_id: str = ""
        self._workspace_id: str = ""
        self._notify_option: str = "NoNotification"

    def dataflow(self, workspace_id: str, dataflow_id: str) -> "RefreshDataflowActivity":
        self._workspace_id = workspace_id
        self._dataflow_id = dataflow_id
        return self

    def notify_on_completion(self) -> "RefreshDataflowActivity":
        self._notify_option = "OnCompletion"
        return self

    def notify_on_failure(self) -> "RefreshDataflowActivity":
        self._notify_option = "OnFailure"
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "dataflowId": self._dataflow_id,
            "workspaceId": self._workspace_id,
            "notifyOption": self._notify_option,
            "dataflowType": "DataflowFabric"
        }
        return activity


class InvokeCopyJobActivity(ActivityBuilder):
    """Builder for InvokeCopyJob activity."""

    def __init__(self, name: str):
        super().__init__(name, "InvokeCopyJob")
        self._copy_job_id: str = ""
        self._workspace_id: str = ""

    def copy_job(self, workspace_id: str, copy_job_id: str) -> "InvokeCopyJobActivity":
        self._workspace_id = workspace_id
        self._copy_job_id = copy_job_id
        return self

    def build(self) -> Dict[str, Any]:
        activity = self._base_activity()
        activity["typeProperties"] = {
            "copyJobId": self._copy_job_id,
            "workspaceId": self._workspace_id
        }
        return activity


# =============================================================================
# PIPELINE BUILDER
# =============================================================================

class PipelineBuilder:
    """
    Builder for complete pipeline definitions.

    Usage:
        pipeline = PipelineBuilder("MyPipeline") \
            .add_activity(copy_activity) \
            .add_activity(foreach_activity) \
            .add_variable("files", "Array", []) \
            .add_parameter("sourceFolder", "String", "data/") \
            .build()
    """

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description
        self._activities: List[Dict[str, Any]] = []
        self._variables: Dict[str, Dict[str, Any]] = {}
        self._parameters: Dict[str, Dict[str, Any]] = {}
        self._annotations: List[str] = []
        self._concurrency: Optional[int] = None

    def add_activity(self, activity: Union[Dict[str, Any], ActivityBuilder]) -> "PipelineBuilder":
        """Add an activity to the pipeline."""
        if isinstance(activity, ActivityBuilder):
            self._activities.append(activity.build())
        else:
            self._activities.append(activity)
        return self

    def add_activities(self, activities: List[Union[Dict[str, Any], ActivityBuilder]]) -> "PipelineBuilder":
        """Add multiple activities."""
        for activity in activities:
            self.add_activity(activity)
        return self

    def add_variable(
        self,
        name: str,
        var_type: str = "String",
        default_value: Any = None
    ) -> "PipelineBuilder":
        """
        Add a pipeline variable.

        Args:
            name: Variable name
            var_type: Type (String, Bool, Array, Object, Int, Float)
            default_value: Default value
        """
        self._variables[name] = {
            "type": var_type,
            "defaultValue": default_value
        }
        return self

    def add_parameter(
        self,
        name: str,
        param_type: str = "String",
        default_value: Any = None
    ) -> "PipelineBuilder":
        """
        Add a pipeline parameter.

        Args:
            name: Parameter name
            param_type: Type (String, Int, Float, Bool, Array, Object, SecureString)
            default_value: Default value
        """
        self._parameters[name] = {
            "type": param_type,
            "defaultValue": default_value
        }
        return self

    def annotation(self, text: str) -> "PipelineBuilder":
        """Add an annotation."""
        self._annotations.append(text)
        return self

    def concurrency(self, max_concurrent: int) -> "PipelineBuilder":
        """Set maximum concurrent runs."""
        self._concurrency = max_concurrent
        return self

    def build(self) -> Dict[str, Any]:
        """Build the complete pipeline definition."""
        pipeline = {
            "properties": {
                "activities": self._activities,
                "annotations": self._annotations
            }
        }

        if self._variables:
            pipeline["properties"]["variables"] = self._variables

        if self._parameters:
            pipeline["properties"]["parameters"] = self._parameters

        if self._concurrency:
            pipeline["properties"]["concurrency"] = self._concurrency

        return pipeline

    def build_for_api(self) -> Dict[str, Any]:
        """
        Build pipeline definition ready for Fabric API.

        Returns the complete structure needed for create/update operations.
        """
        return self.build()
