"""
setup.py — First-time setup script for SiPakar Diet IMT
Run this ONCE after creating the database:
    1. Create the MySQL database:  CREATE DATABASE diet_expert_system;
    2. Run schema.sql:             mysql -u root diet_expert_system < schema.sql
    3. Run this script:            python setup.py
"""

import sys
import pymysql
from werkzeug.security import generate_password_hash

# ── Database config (edit if needed) ──────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': '',           # ← your MySQL root password
    'db':       'diet_expert_system',
    'charset':  'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

def connect():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ Database connection OK.")
        return conn
    except pymysql.err.OperationalError as e:
        print(f"❌ Cannot connect to database: {e}")
        print("   Make sure MySQL is running and database 'diet_expert_system' exists.")
        print("   Then run:  mysql -u root diet_expert_system < schema.sql")
        sys.exit(1)

def create_admin(conn):
    """Create the default admin account."""
    with conn.cursor() as cur:
        cur.execute("SELECT id_user FROM `user` WHERE username = 'admin' LIMIT 1")
        if cur.fetchone():
            print("ℹ️  Admin account already exists (admin / admin123).")
            return

        hashed = generate_password_hash('admin123')
        cur.execute(
            "INSERT INTO `user` (nama, username, password, role) VALUES (%s, %s, %s, %s)",
            ('Administrator', 'admin', hashed, 'admin')
        )
        conn.commit()
        print("✅ Admin account created:  username=admin  password=admin123")

def check_rules(conn):
    """Check how many knowledge base rules exist."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM knowledge_base")
        count = cur.fetchone()['cnt']
        print(f"ℹ️  Knowledge base has {count} rules.")
        if count == 0:
            print("   Run schema.sql first — it contains all 20 default rules.")

def main():
    print("\n══════════════════════════════════════════")
    print("  SiPakar Diet IMT — Setup Script")
    print("══════════════════════════════════════════\n")

    conn = connect()
    create_admin(conn)
    check_rules(conn)
    conn.close()

    print("\n══════════════════════════════════════════")
    print("  Setup complete! Start the app with:")
    print("  python app.py")
    print("  Then open: http://localhost:5000")
    print("══════════════════════════════════════════\n")

if __name__ == '__main__':
    main()
