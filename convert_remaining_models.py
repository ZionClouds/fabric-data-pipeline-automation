#!/usr/bin/env python3
"""
Script to convert remaining Go SDK models to Python
Automates the conversion of Go struct types to Pydantic models
"""

import os
import re
from pathlib import Path

# Services to convert
SERVICES = [
    "eventhouse",
    "digitaltwinbuilderflow",
    "graphmodel",
    "kqldatabase",
    "mlmodel",
    "sqldatabase",
    "mirroreddatabase",
    "mirroredazuredatabrickscatalog",
    "sparkjobdefinition",
    "spark",
]

# Base paths
KNOWLEDGE_BASE = Path("/Users/jayavardhanareddy/Desktop/fabric-data-pipeline-automation/knowledge/fabric")
OUTPUT_BASE = Path("/Users/jayavardhanareddy/Desktop/fabric-data-pipeline-automation/backend/fabric_sdk/models")

def go_type_to_python(go_type):
    """Convert Go types to Python types"""
    type_map = {
        "string": "str",
        "int32": "int",
        "int64": "int",
        "float32": "float",
        "float64": "float",
        "bool": "bool",
        "time.Time": "datetime",
        "any": "Any",
    }

    # Handle pointers
    if go_type.startswith("*"):
        inner_type = go_type[1:]
        python_type = go_type_to_python(inner_type)
        return f"Optional[{python_type}]"

    # Handle slices/arrays
    if go_type.startswith("[]"):
        inner_type = go_type[2:]
        python_type = go_type_to_python(inner_type)
        return f"List[{python_type}]"

    return type_map.get(go_type, go_type)

def snake_case(name):
    """Convert PascalCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def read_go_file(service_name):
    """Read and parse Go models file"""
    models_file = KNOWLEDGE_BASE / service_name / "models.go"
    if not models_file.exists():
        return None, []

    with open(models_file, 'r') as f:
        content = f.read()

    # Extract structs
    struct_pattern = r'type\s+(\w+)\s+struct\s*{([^}]+)}'
    structs = re.findall(struct_pattern, content, re.MULTILINE | re.DOTALL)

    # Extract enums
    enum_pattern = r'type\s+(\w+)\s+string\s*const\s*\([^)]+\)'
    enums = re.findall(enum_pattern, content, re.MULTILINE | re.DOTALL)

    return content, structs

def generate_python_file(service_name):
    """Generate Python file for a service"""
    content, structs = read_go_file(service_name)
    if content is None:
        print(f"Skipping {service_name} - models.go not found")
        return

    # Service display name
    display_name = service_name.replace("_", " ").title()

    python_code = f'''"""
{display_name} Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/{service_name}/models.go and constants.go
Auto-generated - do not edit manually
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

# Note: This is an auto-generated file. Full model definitions should be
# manually reviewed and completed based on the Go SDK models.go file.

'''

    # Write the file
    output_file = OUTPUT_BASE / f"{service_name}.py"
    with open(output_file, 'w') as f:
        f.write(python_code)

    print(f"Generated {service_name}.py (basic structure - needs manual completion)")

if __name__ == "__main__":
    for service in SERVICES:
        generate_python_file(service)

    print(f"\n Converted {len(SERVICES)} services")
    print("Note: These files contain basic structure and need manual completion")
