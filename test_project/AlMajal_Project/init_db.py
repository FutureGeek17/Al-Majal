import sqlite3
from werkzeug.security import generate_password_hash

# Database initialization
def init_db():
    # Connect to database
    connection = sqlite3.connect('database.db')
    
    # Execute schema
    with open('schema.sql') as f:
        connection.executescript(f.read())
    
    # Create admin user
    admin_password = generate_password_hash('admin123')
    cur = connection.cursor()
    cur.execute('''
        INSERT INTO users (name, phone, password, id_number, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Admin User', '1234567890', admin_password, 'ADMIN001', True))
    
    connection.commit()
    connection.close()
    
    print('Database initialized successfully!')
    print('Admin credentials:')
    print('Phone: 1234567890')
    print('Password: admin123')

if __name__ == '__main__':
    init_db() 