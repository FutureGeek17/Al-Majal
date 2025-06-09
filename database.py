import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash

def create_connection():
    try:
        conn = sqlite3.connect('database.db')
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(conn):
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                id_number TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        
        # Create bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                facility TEXT NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(facility, date, time_slot)
            )
        ''')
        
        # Create default admin user if not exists
        cursor.execute('SELECT id FROM users WHERE phone = ?', ('admin',))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (name, id_number, phone, password, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Admin User', 'ADMIN001', 'admin', generate_password_hash('admin123'), True))
        
        conn.commit()
        print("Database tables created successfully")
        
    except Error as e:
        print(f"Error creating tables: {e}")

def main():
    # Create a database connection
    conn = create_connection()
    
    if conn is not None:
        # Create tables
        create_tables(conn)
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main() 