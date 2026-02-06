from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import secrets
from datetime import datetime, timedelta
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL Config
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER') 
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DATABASE')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# 🔥 RISK SENTINEL EMAIL CONFIG
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'risksentinel.help@gmail.com'
app.config['MAIL_PASSWORD'] = 'bqbkvhkltfqxuseo'
app.config['MAIL_DEFAULT_SENDER'] = 'risksentinel.help@gmail.com'
mail = Mail(app)

def send_reset_email(email, token, username):
    try:
        reset_url = f"http://localhost:5000/reset-password/{token}"
        msg = Message(
            subject="🔐 Password Reset - Risk Sentinel",
            sender="risksentinel.help@gmail.com",
            recipients=[email]
        )
        msg.body = f"""
Hello {username},

Reset your Risk Sentinel password: {reset_url}

This link expires in 1 hour.

Best regards,
Risk Sentinel Team
        """
        mail.send(msg)
        print(f"✅ EMAIL sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/enterprise-login', methods=['GET', 'POST'])
def enterprise_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['user_type'] = 'enterprise'
            session['company_name'] = user['username']
            flash('✅ Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('❌ Invalid credentials!', 'error')
    return render_template('auth/enterprise_login.html')

@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vendors WHERE email = %s AND password = %s", (email, password))
        vendor = cur.fetchone()
        cur.close()
        
        if vendor:
            session['user_id'] = vendor['id']
            session['user_type'] = 'vendor'
            session['company_name'] = vendor['company_name']
            flash('✅ Vendor login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('❌ Invalid credentials!', 'error')
    return render_template('auth/vendor_login.html')
@app.route('/enterprise-register', methods=['GET', 'POST'])
def enterprise_register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        role = request.form.get('role', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not all([username, role, email, password]):
            flash('❌ Please fill all fields!', 'error')
            return render_template('auth/enterprise_register.html')
        
        if len(password) < 8:
            flash('❌ Password must be 8+ characters!', 'error')
            return render_template('auth/enterprise_register.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('❌ Invalid email format!', 'error')
            return render_template('auth/enterprise_register.html')
        
        # Check if email already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            flash('❌ Email already registered!', 'error')
            cur.close()
            return render_template('auth/enterprise_register.html')
        cur.close()
        
        # Insert new enterprise user
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, role, email, password, created_date) VALUES (%s, %s, %s, %s, NOW())",
                   (username, role, email, password))
        mysql.connection.commit()
        cur.close()
        
        flash('✅ Enterprise account created! Please login.', 'success')
        return redirect(url_for('enterprise_login'))
    
    return render_template('auth/enterprise_register.html')

@app.route('/vendor-register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not company_name or not email:
            flash('❌ Please fill all fields!', 'error')
            return render_template('auth/vendor_register.html')
        
        if len(company_name) < 2:
            flash('❌ Company name too short!', 'error')
            return render_template('auth/vendor_register.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('❌ Invalid email format!', 'error')
            return render_template('auth/vendor_register.html')
        
        # Check if email already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM vendors WHERE email = %s", (email,))
        if cur.fetchone():
            flash('❌ Email already registered!', 'error')
            cur.close()
            return render_template('auth/vendor_register.html')
        cur.close()
        
        # Insert new vendor (status=active, auto created_date)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO vendors (company_name, email, password, status, created_date) VALUES (%s, %s, %s, 'active', NOW())",
                   (company_name, email, 'default_password_123'))  # Update password logic later
        mysql.connection.commit()
        cur.close()
        
        flash('✅ Vendor account created! Please contact admin to set password.', 'success')
        return redirect(url_for('vendor_login'))
    
    return render_template('auth/vendor_register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('❌ Invalid email!', 'error')
            return render_template('auth/forgot_password.html')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            cur.execute("SELECT id, company_name FROM vendors WHERE email = %s", (email,))
            vendor = cur.fetchone()
            if vendor:
                user = {'user_id': vendor['id'], 'username': vendor['company_name']}
                table_name = 'vendors'
            else:
                flash('❌ Email not found!', 'error')
                cur.close()
                return render_template('auth/forgot_password.html')
        else:
            table_name = 'users'
        
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=1)
        
        cur.execute(f"UPDATE {table_name} SET reset_token = NULL, reset_expires = NULL WHERE email = %s", (email,))
        cur.execute(f"UPDATE {table_name} SET reset_token = %s, reset_expires = %s WHERE email = %s", 
                   (token, expires, email))
        mysql.connection.commit()
        cur.close()
        
        email_sent = send_reset_email(email, token, user['username'])
        if email_sent:
            flash('✅ Check your INBOX for reset link!', 'success')
        else:
            print(f"🔗 URL: http://localhost:5000/reset-password/{token}")
            flash('⚠️ Check console for reset URL.', 'warning')
        
        return render_template('auth/forgot_password.html')
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # ✅ VALIDATE TOKEN FIRST (GET request)
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM users WHERE reset_token = %s AND reset_expires > NOW()", (token,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("SELECT id FROM vendors WHERE reset_token = %s AND reset_expires > NOW()", (token,))
        vendor = cur.fetchone()
        if not vendor:
            flash('❌ Invalid/expired link!', 'error')
            cur.close()
            return redirect(url_for('landing'))
    cur.close()
    
    # ✅ POST request - SAFE form handling
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # ✅ SAFE VALIDATION - no more KeyError!
        if not new_password or not confirm_password:
            flash('❌ Please fill both password fields!', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('❌ Passwords do not match!', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('❌ Password must be 8+ characters!', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id FROM users WHERE reset_token = %s AND reset_expires > NOW()", (token,))
        user = cur.fetchone()
        table_name = None
        
        if user:
            table_name = 'users'
        else:
            cur.execute("SELECT id FROM vendors WHERE reset_token = %s AND reset_expires > NOW()", (token,))
            vendor = cur.fetchone()
            if vendor:
                table_name = 'vendors'
        
        if table_name:
            cur.execute(f"UPDATE {table_name} SET password = %s, reset_token = NULL, reset_expires = NULL WHERE reset_token = %s", 
                       (new_password, token))
            mysql.connection.commit()
            cur.close()
            flash('✅ Password reset successful! Please login.', 'success')
            return redirect(url_for('landing'))
        else:
            flash('❌ Reset link expired!', 'error')
            cur.close()
            return redirect(url_for('landing'))
    
    return render_template('auth/reset_password.html', token=token)

@app.route('/dashboard')
def dashboard():
    if 'user_type' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('landing'))
    get_flashed_messages()
    return render_template('dashboard.html', 
                          user_type=session.get('user_type'),
                          company_name=session.get('company_name'),
                          user_id=session.get('user_id'))

@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Logged out!', 'success')
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True)
