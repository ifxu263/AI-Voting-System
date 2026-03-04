# File: app.py

from flask import Flask, render_template, request, redirect, flash, url_for

app = Flask(__name__)
app.secret_key = 'irfan_secret_key'  # Flash ke liye secret key mandatory hai

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Yaha login logic lagana hoga (abhi simple pass kar rahe hain)
        flash('Login Successful!', 'success')
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Yaha tu database me save kar sakta hai
        print(f'Username: {username}, Password: {password}, Email: {email}')

        flash('Registration Successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
