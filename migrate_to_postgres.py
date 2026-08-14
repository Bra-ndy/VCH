# migrate_to_postgres.py 
import sqlite3 
import psycopg2 
import os 
 
def get_postgres_connection(): 
    database_url = os.environ.get('DATABASE_URL') 
    if not database_url: 
        print("? DATABASE_URL not set") 
        return None 
 
    if database_url.startswith('postgres://'): 
        database_url = database_url.replace('postgres://', 'postgresql://', 1) 
 
    try: 
        conn = psycopg2.connect(database_url) 
        return conn 
    except Exception as e: 
        print(f"? Error connecting to PostgreSQL: {e}") 
        return None 
 
def migrate_data(): 
    print("?? Starting migration...") 
    sqlite_path = 'instance/vch.db' 
    if not os.path.exists(sqlite_path): 
        print("? SQLite database not found") 
        return 
 
    sqlite_conn = sqlite3.connect(sqlite_path) 
    sqlite_conn.row_factory = sqlite3.Row 
    sqlite_cursor = sqlite_conn.cursor() 
 
    pg_conn = get_postgres_connection() 
    if not pg_conn: 
        return 
 
    pg_cursor = pg_conn.cursor() 
    tables = ['users', 'vehicles', 'rentals', 'transactions', 'service_history', 'referral_bonuses', 'notifications', 'activity_logs'] 
 
    try: 
        for table in tables: 
            print(f"?? Migrating {table}...") 
            sqlite_cursor.execute(f"SELECT * FROM {table}") 
            rows = sqlite_cursor.fetchall() 
            if not rows: 
                continue 
            columns = [desc[0] for desc in sqlite_cursor.description] 
            placeholders = ','.join(['%s'] * len(columns)) 
            columns_str = ','.join(columns) 
            inserted = 0 
            for row in rows: 
                values = [row[col] for col in columns] 
                query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})" 
                try: 
                    pg_cursor.execute(query, values) 
                    inserted += 1 
                except: 
                    pass 
            print(f"   ? Migrated {inserted} rows") 
        pg_conn.commit() 
        print("? Migration completed!") 
    except Exception as e: 
        pg_conn.rollback() 
        print(f"? Migration failed: {e}") 
    finally: 
        sqlite_conn.close() 
        pg_conn.close() 
 
if __name__ == '__main__': 
    migrate_data() 
