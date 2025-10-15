import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_SERVER = os.getenv("DATABASE_SERVER", "fabric-server.database.windows.net")
DATABASE_NAME = os.getenv("DATABASE_NAME", "fabricdb")
DATABASE_USER = os.getenv("DATABASE_USER", "fabricadmin")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

# Anthropic Claude Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "8000"))

# Microsoft Fabric Configuration
FABRIC_CLIENT_ID = os.getenv("FABRIC_CLIENT_ID", "0944e22d-d0f1-40c1-a9fc-f422c05949f3")
FABRIC_TENANT_ID = os.getenv("FABRIC_TENANT_ID", "e28d23e3-803d-418d-a720-c0bed39f77b6")
FABRIC_CLIENT_SECRET = os.getenv("FABRIC_CLIENT_SECRET", "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7")

# Workspace Backend Integration
WORKSPACE_BACKEND_URL = os.getenv("WORKSPACE_BACKEND_URL", "https://fabricbackend.lemonfield-12c57489.eastus.azurecontainerapps.io")

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://pipelinebuilder.salmonmushroom-f0022bfd.eastus.azurecontainerapps.io").split(",")

# Development Mode
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false")

# Get database connection string
def get_db_connection_string():
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DATABASE_SERVER};"
        f"DATABASE={DATABASE_NAME};"
        f"UID={DATABASE_USER};"
        f"PWD={DATABASE_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
