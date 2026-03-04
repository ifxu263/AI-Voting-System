import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Delete if already exists (optional)
c.execute('DROP TABLE IF EXISTS events')

# Create with correct structure
c.execute('''
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT,
        is_active INTEGER DEFAULT 0
    )
''')

conn.commit()
conn.close()

print("✅ 'events' table recreated with 'is_active' column.")
