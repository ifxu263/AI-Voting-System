from flask import Flask, render_template, request, redirect, flash, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'irfan_secret_key'

# ================== DATABASE CONNECTION ==================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ================== LOGIN REQUIRED DECORATOR ==================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ================== HOME ==================
@app.route('/')
def home():
    return render_template('index.html')

# ================== USER SIDE ==================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                         (username, hashed_password, email))
            conn.commit()
            flash('Registration Successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login Successful!', 'success')
            return redirect(url_for('vote'))
        else:
            flash('Invalid Credentials', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    conn = get_db_connection()
    user_id = session['user_id']

    # Get active event
    active_event = conn.execute('SELECT * FROM events WHERE is_active = 1').fetchone()

    if not active_event:
        conn.close()
        flash('No active voting event available.', 'warning')
        return redirect(url_for('home'))

    # Check if voting is still open
    end_time_str = active_event['end_time']
    if end_time_str:
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        if datetime.now() > end_time:
            conn.execute('UPDATE events SET is_active = 0 WHERE id = ?', (active_event['id'],))
            conn.commit()
            conn.close()
            flash('Voting period has ended. Please check results.', 'info')
            return redirect(url_for('result'))

    event_id = active_event['id']
    already_voted = conn.execute('SELECT * FROM votes WHERE user_id = ? AND event_id = ?', (user_id, event_id)).fetchone()

    if request.method == 'POST':
        candidate_id = request.form.get('candidate')
        if not candidate_id:
            flash('Please select a candidate before voting.', 'warning')
            return redirect(url_for('vote'))

        if not already_voted:
            conn.execute('INSERT INTO votes (user_id, candidate_id, event_id) VALUES (?, ?, ?)',
                         (user_id, candidate_id, event_id))
            conn.commit()
            conn.close()
            return render_template('wait.html')
        else:
            conn.close()
            flash('You have already voted in this event.', 'info')
            return redirect(url_for('vote'))

    candidates = conn.execute('SELECT * FROM candidates WHERE event_id = ?', (event_id,)).fetchall()
    conn.close()
    return render_template('vote.html', candidates=candidates, already_voted=already_voted, active_event=active_event)

@app.route('/wait')
@login_required
def wait():
    return render_template('wait.html')

@app.route('/result')
@login_required
def result():
    conn = get_db_connection()
    active_event = conn.execute('SELECT * FROM events WHERE is_active = 0 ORDER BY id DESC LIMIT 1').fetchone()
    if not active_event:
        flash('No event to show result.', 'warning')
        return redirect(url_for('home'))

    candidates = conn.execute('''
        SELECT c.name, COUNT(v.id) AS votes
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id AND v.event_id = ?
        WHERE c.event_id = ?
        GROUP BY c.id
    ''', (active_event['id'], active_event['id'])).fetchall()

    conn.close()
    return render_template('result.html', candidates=candidates)

# ================== ADMIN SIDE ==================
ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123'

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
            return redirect(url_for('admin'))
    return render_template('admin_login.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    conn = get_db_connection()

    if request.method == 'POST':
        if 'add_event' in request.form:
            title = request.form['title']
            description = request.form['description']
            date = request.form['date']
            end_time = request.form['end_time']  # format: YYYY-MM-DD HH:MM:SS
            conn.execute('INSERT INTO events (title, description, date, end_time, is_active) VALUES (?, ?, ?, ?, 1)',
                         (title, description, date, end_time))
            conn.commit()
        elif 'delete_event' in request.form:
            event_id = request.form['event_id']
            conn.execute('DELETE FROM votes WHERE event_id = ?', (event_id,))
            conn.execute('DELETE FROM candidates WHERE event_id = ?', (event_id,))
            conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
        elif 'activate_event' in request.form:
            event_id = request.form['event_id']
            conn.execute('UPDATE events SET is_active = 0')
            conn.execute('UPDATE events SET is_active = 1 WHERE id = ?', (event_id,))
            conn.commit()
        elif 'deactivate_event' in request.form:
            event_id = request.form['event_id']
            conn.execute('UPDATE events SET is_active = 0 WHERE id = ?', (event_id,))
            conn.commit()
        elif 'add_candidate' in request.form:
            name = request.form['candidate_name']
            event_id = request.form['event_id']
            conn.execute('INSERT INTO candidates (name, event_id) VALUES (?, ?)', (name, event_id))
            conn.commit()

    events = conn.execute('SELECT * FROM events').fetchall()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', events=events, candidates=candidates)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('home'))

# ================== RUN ==================
if __name__ == '__main__':
    app.run(debug=True)
