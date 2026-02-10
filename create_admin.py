import sqlite3
import getpass
from werkzeug.security import generate_password_hash

DB = 'database.db'

def create_admin():
    name = input('Admin name: ').strip()
    email = input('Admin email: ').strip()
    pw = getpass.getpass('Password: ')
    pw2 = getpass.getpass('Confirm: ')
    if pw != pw2:
        print('Passwords do not match')
        return
    ph = generate_password_hash(pw)
    conn = sqlite3.connect(DB)
    try:
        conn.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)', (name, email, ph, 'admin'))
        conn.commit()
        print('Admin user created')
    except Exception as e:
        print('Error:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin()
