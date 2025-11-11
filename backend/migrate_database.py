"""
Database Migration Script
Adds the 'title' column to the conversations table
"""
import pyodbc
import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Add missing columns to conversations and jobs tables"""
    try:
        # Create connection string
        connection_string = settings.get_db_connection_string()
        logger.info(f"Connecting to database: {settings.DATABASE_SERVER}/{settings.DATABASE_NAME}")

        # Connect to database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # === CONVERSATIONS TABLE ===
        # Check if title column exists
        check_column_sql = """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'conversations'
        AND COLUMN_NAME = 'title'
        """

        cursor.execute(check_column_sql)
        column_exists = cursor.fetchone()[0] > 0

        if column_exists:
            logger.info("OK Column 'title' already exists in conversations table")
        else:
            logger.info("Adding 'title' column to conversations table...")

            # Add title column
            alter_table_sql = """
            ALTER TABLE conversations
            ADD title NVARCHAR(500) NULL
            """

            cursor.execute(alter_table_sql)
            conn.commit()

            logger.info("OK Successfully added 'title' column to conversations table")

            # Update existing records with default title
            update_sql = """
            UPDATE conversations
            SET title = 'New Conversation'
            WHERE title IS NULL
            """

            cursor.execute(update_sql)
            rows_updated = cursor.rowcount
            conn.commit()

            logger.info(f"OK Updated {rows_updated} existing conversations with default title")

        # === JOBS TABLE ===
        # Check if warehouse_id column exists
        check_warehouse_id_sql = """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'jobs'
        AND COLUMN_NAME = 'warehouse_id'
        """

        cursor.execute(check_warehouse_id_sql)
        warehouse_id_exists = cursor.fetchone()[0] > 0

        if not warehouse_id_exists:
            logger.info("Adding 'warehouse_id' column to jobs table...")
            cursor.execute("ALTER TABLE jobs ADD warehouse_id NVARCHAR(255) NULL")
            conn.commit()
            logger.info("OK Successfully added 'warehouse_id' column to jobs table")
        else:
            logger.info("OK Column 'warehouse_id' already exists in jobs table")

        # Check if warehouse_name column exists
        check_warehouse_name_sql = """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'jobs'
        AND COLUMN_NAME = 'warehouse_name'
        """

        cursor.execute(check_warehouse_name_sql)
        warehouse_name_exists = cursor.fetchone()[0] > 0

        if not warehouse_name_exists:
            logger.info("Adding 'warehouse_name' column to jobs table...")
            cursor.execute("ALTER TABLE jobs ADD warehouse_name NVARCHAR(255) NULL")
            conn.commit()
            logger.info("OK Successfully added 'warehouse_name' column to jobs table")
        else:
            logger.info("OK Column 'warehouse_name' already exists in jobs table")

        cursor.close()
        conn.close()

        logger.info("OK Database migration completed successfully")
        return True

    except pyodbc.Error as e:
        logger.error(f"Database error during migration: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration Script")
    print("Adding 'title' column to conversations table")
    print("=" * 60)
    print()

    success = migrate_database()

    print()
    if success:
        print("✓ Migration completed successfully!")
    else:
        print("✗ Migration failed. Please check the logs above.")
    print()
