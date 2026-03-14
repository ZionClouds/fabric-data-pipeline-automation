"""
Centralized Settings Configuration
⚠️ WARNING: This file contains hardcoded secrets and credentials.
⚠️ DO NOT commit this file to git or share publicly!
⚠️ All sensitive values are stored directly in this file.
"""

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_SERVER = "microfabrics.database.windows.net"
DATABASE_NAME = "fabrics"
DATABASE_USER = "fabrics"
DATABASE_PASSWORD = "iLoveFab@143"

# SQLAlchemy Database URL
import os
from urllib.parse import quote_plus

# Use SQLite for local development, Azure SQL for production
USE_LOCAL_DB = os.environ.get("USE_LOCAL_DB", "true").lower() == "true"

if USE_LOCAL_DB:
    # Local SQLite database — no network dependency
    _db_dir = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL = f"sqlite:///{os.path.join(_db_dir, 'fabric_pipeline.db')}"
else:
    # Azure SQL Server (requires firewall rule for your IP)
    encoded_password = quote_plus(DATABASE_PASSWORD)
    DATABASE_URL = (
        f"mssql+pyodbc://{DATABASE_USER}:{encoded_password}"
        f"@{DATABASE_SERVER}/{DATABASE_NAME}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&Encrypt=yes&TrustServerCertificate=yes&Connection+Timeout=30"
    )

# ============================================================================
# GCP VERTEX AI - CLAUDE CONFIGURATION (PRIMARY LLM)
# ============================================================================
GCP_PROJECT_ID = "gemini-for-zion"
GCP_REGION = "us-east5"
CLAUDE_MODEL = "claude-opus-4-6"
CLAUDE_MAX_TOKENS = 16384
CLAUDE_TEMPERATURE = 0.7

# ============================================================================
# AZURE AI FOUNDRY PROJECT (for Agents with Bing Grounding)
# ============================================================================
AZURE_AI_PROJECT_ENDPOINT = "https://fabricfoundary.services.ai.azure.com/api/projects/fabricproject"
AZURE_OPENAI_API_KEY = "Fjzxa9pdfaG4At9cM22RKZZAGxjI309WmFSQVxaypAx5UkRmjxnvJQQJ99BJACHYHv6XJ3w3AAAAACOGXwko"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini-bing"
BING_GROUNDING_CONNECTION_ID = "/subscriptions/df3a2439-dcb9-4a5e-94f1-dfc7094b7894/resourceGroups/uic-omi-dlake-prod-fab-rg/providers/Microsoft.CognitiveServices/accounts/fabricfoundary/projects/fabricproject/connections/fabricbing"

# ============================================================================
# MICROSOFT FABRIC CONFIGURATION
# ============================================================================
FABRIC_CLIENT_ID = "0944e22d-d0f1-40c1-a9fc-f422c05949f3"
FABRIC_TENANT_ID = "e28d23e3-803d-418d-a720-c0bed39f77b6"
FABRIC_CLIENT_SECRET = "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7"

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002"
]

# ============================================================================
# DEVELOPMENT MODE
# ============================================================================
DISABLE_AUTH = True  # Set to False for production

# ============================================================================
# AZURE STORAGE ACCOUNT CONFIGURATION (ADLS Gen2 - Hierarchical Namespace Enabled)
# ============================================================================
STORAGE_ACCOUNT_NAME = "claimsadlsgen2"
STORAGE_ACCOUNT_KEY = "K3YTYoyvIEQvM5LJqnXBeiuUa1Yr/Dj+RCMNJYZySL8OXQVT0DOdJw7j9KvnhAEReGLKDpm0B8Tl+AStXwktmA=="
STORAGE_CONNECTION_STRING = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
STORAGE_CONTAINERS = {
    "bronze": "bronze",
    "silver": "silver"
}
STORAGE_ENDPOINT_SUFFIX = "core.windows.net"
STORAGE_PROTOCOL = "https"

# ============================================================================
# DATABASE CONNECTION STRING HELPER
# ============================================================================
def get_db_connection_string():
    """
    Generate database connection string for SQL Server
    """
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=tcp:{DATABASE_SERVER},1433;"
        f"DATABASE={DATABASE_NAME};"
        f"UID={DATABASE_USER};"
        f"PWD={DATABASE_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )

