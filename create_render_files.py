# create_render_files.py
import os

def create_render_yaml():
    """Create render.yaml file"""
    content = """services:
  - type: web
    name: vch-production
    env: python
    region: oregon
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
      flask db upgrade || echo "Migration skipped"
    startCommand: gunicorn -c gunicorn.conf.py app:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: vch-production-db
          property: connectionString
      - key: ADMIN_NAME
        value: WINNY LANGAT
      - key: ADMIN_MPESA_NUMBER
        value: 0753796259
      - key: ADMIN_MPESA_NUMBER_API
        value: 254753796259
      - key: MPESA_CONSUMER_KEY
        sync: false
      - key: MPESA_CONSUMER_SECRET
        sync: false
      - key: MPESA_PASSKEY
        sync: false
      - key: MPESA_SHORTCODE
        value: 174379
      - key: MPESA_CALLBACK_URL
        value: https://vch-production.onrender.com/payments/mpesa/callback
      - key: MPESA_ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
    healthCheckPath: /health
    autoDeploy: true
    disk:
      name: vch-logs
      mountPath: /var/log
      sizeGB: 1

  - type: postgresql
    name: vch-production-db
    region: oregon
    database: vch_production
    user: vch_prod_user
    plan: pro
    highAvailability: true
    diskSizeGB: 10
    autoScaling:
      enabled: true
      maxSizeGB: 50
    backupSchedule: "0 0 * * *"
    envVars:
      - key: PGDATABASE
        value: vch_production
      - key: PGUSER
        value: vch_prod_user

  - type: redis
    name: vch-production-redis
    region: oregon
    plan: starter
    maxmemoryPolicy: allkeys-lru
"""
    
    with open('render.yaml', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created render.yaml")

def create_gunicorn_conf():
    """Create gunicorn.conf.py file"""
    content = """# gunicorn.conf.py
import os
import multiprocessing

port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
threads = 2

timeout = 120
graceful_timeout = 30

max_requests = 1000
max_requests_jitter = 100

accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')

preload_app = True
worker_tmp_dir = '/dev/shm'
forwarded_allow_ips = '*'
"""
    
    with open('gunicorn.conf.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created gunicorn.conf.py")

def create_migration_script():
    """Create migrate_to_postgres.py file"""
    content = """# migrate_to_postgres.py
import sqlite3
import psycopg2
import os

def get_postgres_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return None
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return None

def migrate_data():
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    sqlite_path = 'instance/vch.db'
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        return
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    pg_conn = get_postgres_connection()
    if not pg_conn:
        return
    
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SET session_replication_role = 'replica';")
    
    tables = ['users', 'vehicles', 'rentals', 'transactions', 
              'service_history', 'referral_bonuses', 'notifications', 'activity_logs']
    
    try:
        for table in tables:
            print(f"📦 Migrating {table}...")
            
            pg_cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                );
            """)
            table_exists = pg_cursor.fetchone()[0]
            
            if not table_exists:
                print(f"   ⚠️ Table {table} doesn't exist, skipping...")
                continue
            
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"   ⚠️ No data in {table}")
                continue
            
            columns = [desc[0] for desc in sqlite_cursor.description]
            placeholders = ','.join(['%s'] * len(columns))
            columns_str = ','.join(columns)
            
            inserted = 0
            for row in rows:
                values = [row[col] for col in columns]
                values = [None if v == '' else v for v in values]
                query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                try:
                    pg_cursor.execute(query, values)
                    inserted += 1
                except Exception as e:
                    print(f"   ⚠️ Error inserting row: {str(e)[:100]}...")
            
            print(f"   ✅ Migrated {inserted} rows from {table}")
        
        pg_conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
    finally:
        pg_cursor.execute("SET session_replication_role = 'origin';")
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    migrate_data()
"""
    
    with open('migrate_to_postgres.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created migrate_to_postgres.py")

def create_requirements_txt():
    """Create requirements.txt file"""
    content = """# Core
Flask==2.3.2
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-Migrate==4.0.4
Flask-Mail==0.9.1
Flask-Caching==2.1.0
Flask-SocketIO==5.3.4
Flask-WTF==1.1.1

# Database
psycopg2-binary==2.9.7
SQLAlchemy==2.0.20
alembic==1.11.3

# WSGI Server
gunicorn==21.2.0
eventlet==0.33.3
python-socketio==5.8.0

# Utilities
python-dotenv==1.0.0
WTForms==3.0.1
requests==2.31.0
Pillow==10.0.0

# M-Pesa & Payments
pyjwt==2.8.0
cryptography==41.0.3

# Production Monitoring
prometheus-client==0.18.0
"""
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created requirements.txt")

def create_procfile():
    """Create Procfile for Render"""
    content = """web: gunicorn -c gunicorn.conf.py app:app
"""
    
    with open('Procfile', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created Procfile")

def main():
    print("📁 Creating deployment files...")
    print("-" * 40)
    
    create_render_yaml()
    create_gunicorn_conf()
    create_migration_script()
    create_requirements_txt()
    create_procfile()
    
    print("-" * 40)
    print("✅ All files created successfully!")
    print("\n📋 Files created:")
    print("  - render.yaml")
    print("  - gunicorn.conf.py")
    print("  - migrate_to_postgres.py")
    print("  - requirements.txt")
    print("  - Procfile")
    print("\n🚀 Next steps:")
    print("1. git add .")
    print("2. git commit -m 'Add Render deployment files'")
    print("3. git push")
    print("4. Deploy on Render using render.yaml")

if __name__ == '__main__':
    main()