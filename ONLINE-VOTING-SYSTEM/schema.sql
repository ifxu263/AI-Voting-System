DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS events;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    date TEXT NOT NULL,
    is_active INTEGER DEFAULT 0
    ALTER TABLE events ADD COLUMN end_time TEXT;

);

CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(candidate_id) REFERENCES candidates(id),
    FOREIGN KEY(event_id) REFERENCES events(id)
);
ALTER TABLE events ADD COLUMN end_time TEXT;

