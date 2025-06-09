import sqlite3

def check_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("Checking users table:")
    users = cur.execute('SELECT id, name, phone, password, is_admin FROM users').fetchall()
    for user in users:
        print(f"ID: {user['id']}")
        print(f"Name: {user['name']}")
        print(f"Phone: {user['phone']}")
        print(f"Password hash: {user['password'][:30]}...")
        print(f"Is admin: {user['is_admin']}")
        print("-" * 50)
    
    conn.close()

if __name__ == '__main__':
    check_db() 