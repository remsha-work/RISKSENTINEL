from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# MySQL Config
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DATABASE', 'risk_sentinel')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# SMTP Config (from your separate SMTP details file)
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'

RESET_TOKEN_SER = URLSafeTimedSerializer(app.secret_key)

# 🔥 COMPLETE ROLE MAPPING
ROLE_DASHBOARDS = {
    'admin': 'Admin_Dashboard.html',
    'analyst': 'analyst_Dashboard.html', 
    'pm': 'PM_Dashboard.html',
    'tl': 'TL_Dashboard.html',
    'senior_dev': 'Senior_Developer_Dashboard.html',
    'junior_dev': 'junior_Developer_Dashboard.html',
    'vendor': 'vendor_Dashboard.html'
}

# Email sending function
def send_reset_email(user_id, email, username):
    """Send password reset email using SMTP config"""
    try:
        token = RESET_TOKEN_SER.dumps(user_id, salt='password-reset')
        reset_url = f"http://localhost:5000/reset-password/{token}"
        
        msg = MIMEMultipart()
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = "Risk Sentinel - Password Reset"
        
        body = f"""
Hi {username},

Click here to reset your password: {reset_url}

This link expires in 1 hour.

Risk Sentinel Team
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        if MAIL_USERNAME and MAIL_PASSWORD:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ===== LANDING PAGE =====
@app.route('/')
def landing():
    return render_template('landing.html')

# ===== ENTERPRISE LOGIN/REGISTER =====
@app.route('/enterprise-login', methods=['GET', 'POST'])
def enterprise_login():
    if 'user_id' in session:
        return redirect(f'/{session["role"]}-dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, username, role, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and user['password'] == password:  # TODO: Use bcrypt hashing
            session['user_id'] = user['user_id']
            session['role'] = user['role'].lower().replace(' ', '_')
            session['username'] = user['username']
            return redirect(f'/{session["role"]}-dashboard')
        
        return render_template('auth/enterprise_login.html', error="Invalid credentials")
    return render_template('auth/enterprise_login.html')

@app.route('/enterprise-register', methods=['GET', 'POST'])
def enterprise_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'pm')
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (username, email, password, role))  # TODO: Hash password
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Please login.', 'success')
            return redirect('/enterprise-login')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('auth/enterprise_registration.html')

# ===== VENDOR LOGIN/REGISTER =====
@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, username, role, password FROM users WHERE email = %s AND role = 'vendor'", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['user_id']
            session['role'] = 'vendor'
            session['username'] = user['username']
            return redirect('/vendor-dashboard')
        
        return render_template('auth/vendor_login.html', error="Invalid credentials")
    return render_template('auth/vendor_login.html')

@app.route('/vendor-register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'vendor')", 
                       (username, email, password))
            mysql.connection.commit()
            cur.close()
            flash('Vendor registration successful!', 'success')
            return redirect('/vendor-login')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('auth/vendor_registration.html')

# 🔥 PASSWORD RESET ROUTES
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, username, email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and send_reset_email(user['user_id'], user['email'], user['username']):
            flash('✅ Reset link sent to your email!', 'success')
        else:
            flash('❌ Failed to send email or email not found', 'error')
        
        return redirect(url_for('forgot_password'))
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('auth/reset_password.html', token=token, error='Passwords do not match!')
        
        try:
            user_id = RESET_TOKEN_SER.loads(token, salt='password-reset', max_age=3600)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (password, user_id))
            mysql.connection.commit()
            cur.close()
            flash('✅ Password reset successful!', 'success')
            return redirect(url_for('enterprise_login'))
        except:
            flash('❌ Invalid or expired link', 'error')
            return redirect(url_for('forgot_password'))
    
    return render_template('auth/reset_password.html', token=token)

# 🔥 UNIVERSAL DASHBOARD ROUTING
@app.route('/<role>-dashboard')
@app.route('/<role>-dashboard/<path:subpath>')
def universal_dashboard(role, subpath=None):
    if 'user_id' not in session or session.get('role') != role:
        return redirect('/enterprise-login')
    
    context = get_role_data(role)
    
    page_map = {
        'tasks': 'universal_tasks.html',
        'risks': 'universal_risks.html', 
        'reports': 'universal_reports.html',
        'chat': 'universal_chat.html'
    }
    
    if subpath in page_map:
        template = f'dashboards/{page_map[subpath]}'
    else:
        template = f'dashboards/{ROLE_DASHBOARDS.get(role, "analyst_Dashboard.html")}'
    
    try:
        return render_template(template, **context)
    except Exception as e:
        print(f"Template error: {e}")
        return f"<h1>Page under construction: /{role}-dashboard/{subpath}</h1>", 200

# 🔥 TASKS API - FULL CRUD
@app.route('/api/<role>/tasks', methods=['GET', 'POST'])
def api_tasks(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        data = request.json
        cur.execute("""
            INSERT INTO tasks (title, description, status, priority, assigned_to, created_by, project_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data['title'], data.get('description'), data['status'], data['priority'], 
              data.get('assigned_to'), session['user_id'], data.get('project_id', 1)))
        mysql.connection.commit()
        task_id = cur.lastrowid
        cur.close()
        return jsonify({'success': True, 'task_id': task_id})
    
    # GET all tasks with user names
    cur.execute("""
        SELECT t.*, u1.username as assigned_name, u2.username as created_name 
        FROM tasks t 
        LEFT JOIN users u1 ON t.assigned_to = u1.user_id
        LEFT JOIN users u2 ON t.created_by = u2.user_id
        ORDER BY 
            CASE t.priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                WHEN 'Low' THEN 4 
            END,
            t.created_at DESC
    """)
    tasks = cur.fetchall()
    cur.close()
    return jsonify({'tasks': tasks})
@app.route('/api/users')
def api_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT user_id, username, role 
        FROM users 
        WHERE role IN ('PM','Analyst','TL','SeniorDev','JuniorDev')
        ORDER BY role, username
    """)
    users = cur.fetchall()
    cur.close()
    return jsonify({'users': users})
'''
@app.route('/api/<role>/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def api_task_detail(role, task_id):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    if request.method == 'DELETE':
        cur.execute("DELETE FROM tasks WHERE task_id = %s AND (assigned_to = %s OR created_by = %s)", 
                   (task_id, session['user_id'], session['user_id']))
        deleted = cur.rowcount > 0
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': deleted})
    
    # UPDATE
    data = request.json
    cur.execute("""
        UPDATE tasks SET title=%s, description=%s, status=%s, priority=%s, assigned_to=%s
        WHERE task_id=%s AND (assigned_to=%s OR created_by=%s)
    """, (data['title'], data.get('description'), data['status'], data['priority'],
          data.get('assigned_to'), task_id, session['user_id'], session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True})
'''
@app.route('/api/<role>/tasks/<int:task_id>', methods=['PUT', 'DELETE', 'PATCH'])
def api_task_detail(role, task_id):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    if request.method == 'DELETE':
        cur.execute("DELETE FROM tasks WHERE task_id = %s AND (assigned_to = %s OR created_by = %s)", 
                   (task_id, session['user_id'], session['user_id']))
        deleted = cur.rowcount > 0
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': deleted})
    
    # FULL UPDATE (title, description, status, priority, assigned_to, due_date)
    data = request.json
    cur.execute("""
        UPDATE tasks 
        SET title=%s, description=%s, status=%s, priority=%s, 
            assigned_to=%s, due_date=%s
        WHERE task_id=%s AND (assigned_to=%s OR created_by=%s)
    """, (data['title'], data.get('description'), data['status'], 
          data['priority'], data.get('assigned_to'), data.get('due_date'),
          task_id, session['user_id'], session['user_id']))
    
    updated = cur.rowcount > 0
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': updated})


# 🧠 Role-specific data
def get_role_data(role):
    try:
        cur = mysql.connection.cursor()
        context = {
            'username': session.get('username', role.title()),
            'role': role,
            'active_risks': 0,
            'high_risks': 0,
            'status_data': [],
            'avg_risk_score': 0.0
        }
        
        if role == 'analyst':
            cur.execute("SELECT COUNT(*) as total FROM risks WHERE status != 'Resolved'")
            context['active_risks'] = cur.fetchone()['total'] or 0
            cur.execute("SELECT COUNT(*) as high FROM risks WHERE risk_score >= 8")
            context['high_risks'] = cur.fetchone()['high'] or 0
            cur.execute("SELECT AVG(risk_score) as avg_score FROM risks")
            context['avg_risk_score'] = round(cur.fetchone()['avg_score'] or 0, 1)
        
        cur.execute("SELECT status, COUNT(*) as count FROM risks GROUP BY status")
        context['status_data'] = cur.fetchall()
        cur.close()
        return context
    except:
        return {
            'username': session.get('username', 'User'),
            'role': role,
            'active_risks': 12,
            'high_risks': 3,
            'status_data': [],
            'avg_risk_score': 7.2
        }

# ✅ LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ✅ ERROR HANDLING
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# 🔥 ANALYTICS DASHBOARD APIs (PHASE 1)
'''
@app.route('/api/<role>/analytics/overview')
def api_analytics_overview(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    # Your actual data (matches your tables perfectly)
    cur.execute("""
        SELECT 
            COUNT(*) as total_risks,
            SUM(CASE WHEN status IN ('Identified','Open','InProgress') THEN 1 ELSE 0 END) as active_risks,
            SUM(CASE WHEN risk_score >= 3 OR rag_status = 'Red' THEN 1 ELSE 0 END) as high_risks,
            ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score,
            COUNT(DISTINCT project_id) as total_projects,
            SUM(CASE WHEN status = 'NotStarted' OR status = 'InProgress' THEN 1 ELSE 0 END) as pending_tasks
        FROM risks
    """)
    overview = cur.fetchone()
    
    # Tasks overview
    cur.execute("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status IN ('NotStarted','InProgress') THEN 1 ELSE 0 END) as active_tasks,
            SUM(CASE WHEN due_date < CURDATE() AND status != 'Completed' THEN 1 ELSE 0 END) as overdue_tasks
        FROM tasks
    """)
    tasks_data = cur.fetchone()
    
    cur.close()
    return jsonify({
        **overview,
        'total_tasks': tasks_data['total_tasks'],
        'active_tasks': tasks_data['active_tasks'],
        'overdue_tasks': tasks_data['overdue_tasks']
    })

@app.route('/api/<role>/analytics/trends')
def api_analytics_trends(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            DATE(created_at) as date, 
            COUNT(*) as new_risks,
            ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score,
            COUNT(CASE WHEN status IN ('Identified','Open','InProgress') THEN 1 END) as active_risks
        FROM risks 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
    """)
    trends = cur.fetchall()
    cur.close()
    return jsonify({'trends': trends})

@app.route('/api/<role>/analytics/status')
def api_analytics_status(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    # Risk status distribution
    cur.execute("""
        SELECT status, COUNT(*) as count, 
               ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score
        FROM risks 
        GROUP BY status 
        ORDER BY 
            CASE status 
                WHEN 'Identified' THEN 1
                WHEN 'Open' THEN 2 
                WHEN 'InProgress' THEN 3
                WHEN 'Mitigated' THEN 4
                WHEN 'Closed' THEN 5
            END
    """)
    risk_status = cur.fetchall()
    
    # Task status distribution  
    cur.execute("""
        SELECT status, COUNT(*) as count
        FROM tasks 
        GROUP BY status
    """)
    task_status = cur.fetchall()
    
    cur.close()
    return jsonify({
        'risk_status': risk_status,
        'task_status': task_status
    })
'''
@app.route('/api/<role>/analytics/overview')
def api_analytics_overview(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    # FIXED: Match YOUR actual table structure
    cur.execute("""
        SELECT 
            COUNT(*) as total_risks,
            SUM(CASE WHEN status IN ('Open','InProgress','Identified') THEN 1 ELSE 0 END) as active_risks,
            SUM(CASE WHEN risk_score >= 4 OR rag_status = 'Red' THEN 1 ELSE 0 END) as high_risks,
            ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score
        FROM risks
    """)
    overview = cur.fetchone()
    
    # FIXED: Match YOUR tasks table structure
    cur.execute("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status IN ('NotStarted','InProgress') THEN 1 ELSE 0 END) as active_tasks,
            SUM(CASE WHEN due_date < CURDATE() AND status != 'Completed' THEN 1 ELSE 0 END) as overdue_tasks
        FROM tasks
    """)
    tasks_data = cur.fetchone()
    
    cur.close()
    return jsonify({
        **dict(overview),  # Convert DictCursor to dict
        'total_tasks': tasks_data['total_tasks'],
        'active_tasks': tasks_data['active_tasks'],
        'overdue_tasks': tasks_data['overdue_tasks']
    })

@app.route('/api/<role>/analytics/trends')
def api_analytics_trends(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            DATE(created_at) as date, 
            COUNT(*) as new_risks,
            ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score
        FROM risks 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
    """)
    trends = cur.fetchall()
    cur.close()
    return jsonify({'trends': trends})

@app.route('/api/<role>/analytics/status')
def api_analytics_status(role):
    if session.get('role') != role:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur = mysql.connection.cursor()
    
    # FIXED: Your actual status values
    cur.execute("""
        SELECT status, COUNT(*) as count, ROUND(AVG(COALESCE(risk_score, 0)), 1) as avg_score
        FROM risks 
        GROUP BY status 
        ORDER BY FIELD(status, 'Identified', 'Open', 'InProgress', 'Mitigated', 'Closed')
    """)
    risk_status = cur.fetchall()
    
    # FIXED: Your actual task statuses
    cur.execute("""
        SELECT status, COUNT(*) as count
        FROM tasks 
        GROUP BY status
    """)
    task_status = cur.fetchall()
    
    cur.close()
    return jsonify({
        'risk_status': risk_status,
        'task_status': task_status
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
