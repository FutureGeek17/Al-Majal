import sqlite3
import logging
import bcrypt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        id_number TEXT UNIQUE NOT NULL,
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create activities table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        duration INTEGER NOT NULL,
        status TEXT DEFAULT 'active'
    )
    ''')
    
    # Create bookings table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        participants INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'confirmed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (activity_id) REFERENCES activities (id)
    )
    ''')

    # Check if admin exists
    admin = conn.execute('SELECT * FROM users WHERE phone = ?', ('1234567890',)).fetchone()
    
    if not admin:
        # Create admin user
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        conn.execute('''
            INSERT INTO users (name, phone, password, id_number, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin User', '1234567890', hashed_password, 'ADMIN001', True))
        logger.info('Admin user created')
    else:
        logger.info('Admin user already exists')
        logger.info('Successfully verified admin user exists')
        logger.info(f'Admin ID: {admin["id"]}')
        logger.info(f'Admin phone: {admin["phone"]}')

    # Initialize activities if they don't exist
    activities = [
        (1, 'Padel Courts', 'Professional padel courts with high-quality surfaces', 'court_sports', 4, 60),
        (2, 'Basketball Court', 'Full-size basketball court that can also be used for volleyball', 'court_sports', 10, 60),
        (3, 'Table Tennis', 'Professional table tennis tables in air-conditioned room', 'indoor', 4, 30),
        (4, 'Mini Golf', 'Fun mini golf course with various challenges', 'indoor', 4, 45),
        (5, 'Football Field', 'Full-size football field with artificial turf', 'court_sports', 14, 60)
    ]
    
    for activity in activities:
        existing = conn.execute('SELECT id FROM activities WHERE id = ?', (activity[0],)).fetchone()
        if not existing:
            conn.execute('''
                INSERT INTO activities (id, name, description, type, capacity, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', activity)
            logger.info(f'Activity {activity[1]} created')
        else:
            logger.info(f'Activity {activity[1]} already exists')

    conn.commit()
    print('Database initialized successfully!')
    print('Admin credentials:')
    print('Password: admin123')

if __name__ == '__main__':
    init_db() 