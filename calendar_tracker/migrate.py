import sqlite3
from models import init_db, migrate_existing_data
from utils import get_db_connection

def migrate_database():
    """Perform database migration"""
    print("Starting database migration...")
    
    try:
        # Initialize new tables and columns
        init_db()
        print("✓ Database schema updated")
        
        # Migrate existing habits to calendar events
        migrate_existing_data()
        print("✓ Existing habits migrated to calendar events")
        
        # Verify migration
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Check tables exist
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            required_tables = ['habits', 'habit_tracking', 'chat_history', 'calendar_events']
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                print(f"⚠️ Warning: Missing tables: {', '.join(missing_tables)}")
            else:
                print("✓ All required tables present")
            
            # Check for successful data migration
            c.execute("SELECT COUNT(*) FROM habits")
            habits_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM calendar_events")
            events_count = c.fetchone()[0]
            
            print(f"\nMigration Summary:")
            print(f"- Total habits: {habits_count}")
            print(f"- Calendar events: {events_count}")
        
        print("\n✨ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        print("Rolling back changes...")
        raise

if __name__ == '__main__':
    migrate_database()
