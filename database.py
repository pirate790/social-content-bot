import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    paid INTEGER DEFAULT 0,
    paid_until TEXT,
    trial_count INTEGER DEFAULT 0,
    joined_date TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    prompt TEXT,
    generated_posts TEXT,
    status TEXT DEFAULT 'Draft',
    created_date TEXT,
    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
)
''')

conn.commit()
conn.close()
print("Database created successfully!")
