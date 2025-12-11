"""
Fabric SDK Activities Package

Contains activity builders for data pipeline automation.
These builders generate the correct JSON structure for Fabric pipeline activities.
"""

from fabric_sdk.activities.activity_builders import (
    # Base
    ActivityBuilder,
    # Data Movement
    CopyActivity,
    InvokeCopyJobActivity,
    # Control Flow
    ForEachActivity,
    IfConditionActivity,
    SwitchActivity,
    UntilActivity,
    WaitActivity,
    FailActivity,
    # Variables
    SetVariableActivity,
    AppendVariableActivity,
    FilterActivity,
    # Data Operations
    GetMetadataActivity,
    LookupActivity,
    ScriptActivity,
    # Fabric Specific
    NotebookActivity,
    RefreshDataflowActivity,
    # External
    WebActivity,
    ExecutePipelineActivity,
    Office365EmailActivity,
    # Pipeline Builder
    PipelineBuilder,
)

__all__ = [
    # Base
    "ActivityBuilder",
    # Data Movement
    "CopyActivity",
    "InvokeCopyJobActivity",
    # Control Flow
    "ForEachActivity",
    "IfConditionActivity",
    "SwitchActivity",
    "UntilActivity",
    "WaitActivity",
    "FailActivity",
    # Variables
    "SetVariableActivity",
    "AppendVariableActivity",
    "FilterActivity",
    # Data Operations
    "GetMetadataActivity",
    "LookupActivity",
    "ScriptActivity",
    # Fabric Specific
    "NotebookActivity",
    "RefreshDataflowActivity",
    # External
    "WebActivity",
    "ExecutePipelineActivity",
    "Office365EmailActivity",
    # Pipeline Builder
    "PipelineBuilder",
]
