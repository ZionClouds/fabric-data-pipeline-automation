"""
Database initialization script
Run this script to create the database tables
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.database_service import init_database
from settings import DATABASE_URL


def main():
    """Initialize database tables"""
    print("Initializing database...")
    print(f"Database URL: {DATABASE_URL}")

    try:
        db_service = init_database(DATABASE_URL)
        print("[SUCCESS] Database tables created successfully!")
        print("\nTables created:")
        print("  - conversations")
        print("  - conversation_messages")
        print("  - jobs")
        print("  - logs")

    except Exception as e:
        print(f"[ERROR] Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
