from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER') 
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DATABASE')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def landing():
    return render_template('landing.html')

# ENTERPRISE - Perfect connection
@app.route('/enterprise-login', methods=['GET', 'POST'])
def enterprise_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        user_data = cur.fetchone()
        cur.close()
        if user_data and check_password_hash(user_data['password_hash'], password):
            session['user_id'] = user_data['id']
            session['user_type'] = 'enterprise'
            session['company_name'] = user_data.get('company_name', user_data.get('name', 'Enterprise'))
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password!', 'error')
    return render_template('auth/enterprise_login.html')

@app.route('/enterprise-register', methods=['GET', 'POST'])
def enterprise_register():
    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user (company_name, email, password_hash) VALUES (%s, %s, %s)",
                       (company_name, email, password_hash))
            mysql.connection.commit()
            cur.close()
            flash('Enterprise account created! Please login.', 'success')
            return redirect(url_for('enterprise_login'))
        except:
            flash('Registration failed! Email already exists.', 'error')
    return render_template('auth/enterprise_register.html')

# VENDOR - Perfect connection  
@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vendors WHERE email = %s", (email,))
        vendor_data = cur.fetchone()
        cur.close()
        if vendor_data and check_password_hash(vendor_data['password_hash'], password):
            session['user_id'] = vendor_data['id']
            session['user_type'] = 'vendor'
            session['company_name'] = vendor_data.get('company_name', 'Vendor')
            flash('Vendor login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password!', 'error')
    return render_template('auth/vendor_login.html')

@app.route('/vendor-register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO vendors (company_name, email, password_hash) VALUES (%s, %s, %s)",
                       (company_name, email, password_hash))
            mysql.connection.commit()
            cur.close()
            flash('Vendor account created! Please login.', 'success')
            return redirect(url_for('vendor_login'))
        except:
            flash('Registration failed! Email already exists.', 'error')
    return render_template('auth/vendor_register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_type' not in session:
        return redirect(url_for('landing'))
    return render_template('dashboard.html', 
                         user_type=session.get('user_type'),
                         company_name=session.get('company_name'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True)
