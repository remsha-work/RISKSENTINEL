from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, date
from dateutil import parser  # Add this import for date parsing

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

# SMTP Config
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'

RESET_TOKEN_SER = URLSafeTimedSerializer(app.secret_key)

ROLE_DASHBOARDS = {
    'admin': 'admin_dashboard.html',
    'analyst': 'analyst_dashboard.html', 
    'pm': 'pm_dashboard.html',
    'tl': 'TL_Dashboard.html',
    'senior_dev': 'Senior_Developer_Dashboard.html',
    'junior_dev': 'junior_Developer_Dashboard.html',
    'vendor': 'vendor_Dashboard.html'
}

def get_role_data(role):
    try:
        cur = mysql.connection.cursor()
        context = {
            'username': session.get('username', role.title()),
            'role': role,
            'total_risks': 127, 'high_risks': 23, 'avg_severity': 7.4, 'mitigated': 89,
            'risks': [], 'status_data': [], 'total_projects': 0, 'overdue_tasks': 0,
            'total_tasks': 0, 'projects': [],
            'team_members': 0, 'total_budget': 0
        }
        
        if role == 'pm':
            user_id = session.get('user_id')
            
            # Total Projects
            cur.execute("SELECT COUNT(*) as total FROM projects WHERE pm_user_id = %s", (user_id,))
            context['total_projects'] = cur.fetchone()['total'] or 0
            
            # Recent Projects
            cur.execute("""
                SELECT project_id, name, status, budget_total, budget_spent, 
                       charter_status, start_date, end_date, created_at
                FROM projects WHERE pm_user_id = %s ORDER BY created_at DESC LIMIT 5
            """, (user_id,))
            context['projects'] = cur.fetchall()
            
            # Team Members
            cur.execute("""
                SELECT COUNT(DISTINCT t.assigned_to) as team_count 
                FROM tasks t JOIN projects p ON t.project_id = p.project_id
                WHERE p.pm_user_id = %s
            """, (user_id,))
            context['team_members'] = cur.fetchone()['team_count'] or 1

        cur.execute("SELECT status, COUNT(*) as count FROM risks GROUP BY status")
        context['status_data'] = cur.fetchall()
        cur.close()
        return context
        
    except Exception as e:
        print(f"get_role_data error: {e}")
        return {'username': session.get('username', 'User'), 'role': role, 'total_projects': 0, 'projects': []}

# 🔥 NEW HELPER FUNCTION
def calculate_task_stats(tasks):
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == 'Completed'])
    pending_tasks = len([t for t in tasks if t['status'] in ['NotStarted', 'InProgress', 'Testing']])
    
    # Add formatted dates and overdue status
    today = date.today()
    for task in tasks:
        if task['due_date']:
            try:
                due_date = parser.parse(task['due_date']).date()
                task['due_date_formatted'] = due_date.strftime('%b %d, %Y')
                task['is_overdue'] = due_date < today and task['status'] != 'Completed'
            except:
                task['due_date_formatted'] = 'Invalid date'
                task['is_overdue'] = False
        else:
            task['due_date_formatted'] = 'No date'
            task['is_overdue'] = False
    
    return total_tasks, completed_tasks, pending_tasks

# ===== ROUTES =====
@app.route('/')
def landing():
    return render_template('landing.html')

# AUTH ROUTES (UNCHANGED - WORKING)
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
        if user and user['password'] == password:
            session['user_id'] = user['user_id']
            session['role'] = user['role'].lower().replace(' ', '_')
            session['username'] = user['username']
            print(f"LOGIN: {email} → {session['role']}-dashboard")
            return redirect(f'/{session["role"]}-dashboard')
        return render_template('auth/enterprise_login.html', error="Invalid credentials")
    return render_template('auth/enterprise_login.html')

@app.route('/enterprise-register', methods=['GET', 'POST'])
def enterprise_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'analyst')
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (username, email, password, role))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Please login.', 'success')
            return redirect('/enterprise-login')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    return render_template('auth/enterprise_registration.html')

@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login():
    if 'user_id' in session: 
        return redirect('/vendor-dashboard')
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
            flash('Vendor registration successful! Please login.', 'success')
            return redirect('/vendor-login')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    return render_template('auth/vendor_registration.html')

# 🔥 PM DASHBOARD ROUTES (PERFECT ✅)
@app.route('/pm-dashboard')
@app.route('/pm_dashboard')
def pm_dashboard():
    if 'user_id' not in session or session.get('role') != 'pm':
        flash('Access denied. PM login required.', 'error')
        return redirect('/enterprise-login')
    
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as total FROM projects WHERE pm_user_id = %s", (user_id,))
    total_projects = cur.fetchone()['total'] or 0
    
    cur.execute("""
        SELECT project_id, name, status, budget_total, budget_spent, 
               charter_status, start_date, end_date, created_at
        FROM projects WHERE pm_user_id = %s ORDER BY created_at DESC LIMIT 5
    """, (user_id,))
    projects = cur.fetchall()
    cur.close()
    
    return render_template('dashboards/pm_dashboard.html', 
                         projects=projects, total_projects=total_projects,
                         total_tasks=0, overdue_tasks=0, total_budget=0, team_members=1)

# 🔥 PM TASKS ROUTE (FIXED ✅)
@app.route('/pm_tasks')
def pm_tasks():
    if 'user_id' not in session or session.get('role') != 'pm':
        flash('Access denied. PM login required.', 'error')
        return redirect('/enterprise-login')
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    # Get PM's projects
    cur.execute("SELECT project_id, name FROM projects WHERE pm_user_id = %s", (user_id,))
    projects = cur.fetchall()
    
    # Get tasks for PM's projects + JOIN with users
    cur.execute("""
        SELECT t.*, p.name as project_name, u.username as assigned_to_name
        FROM tasks t 
        JOIN projects p ON t.project_id = p.project_id
        LEFT JOIN users u ON t.assigned_to = u.user_id
        WHERE p.pm_user_id = %s
        ORDER BY t.due_date ASC, t.created_at DESC
    """, (user_id,))
    tasks = cur.fetchall()
    
    # Calculate stats with formatted dates
    total_tasks, completed_tasks, pending_tasks = calculate_task_stats(tasks)
    
    cur.close()
    return render_template('dashboards/universal_tasks.html', 
                         tasks=tasks, projects=projects,
                         total_tasks=total_tasks, 
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks)

# 🔥 PROJECT CRUD ROUTES (PERFECT ✅)
@app.route('/create_project', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        cur = mysql.connection.cursor()
        project_name = request.form['project_name']
        status = request.form.get('status', 'Planning')
        budget_total = float(request.form.get('budget_total', 0) or 0) * 100000
        budget_spent = float(request.form.get('budget_spent', 0) or 0) * 100000
        start_date = request.form.get('start_date') or None
        end_date = request.form.get('end_date') or None
        charter_status = request.form.get('charter_status', 'Draft')
        stakeholder_list = request.form.get('stakeholder_list', '')
        
        cur.execute("""
            INSERT INTO projects (name, pm_user_id, status, budget_total, budget_spent, 
                                start_date, end_date, charter_status, stakeholder_list)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (project_name, session['user_id'], status, budget_total, budget_spent, 
              start_date, end_date, charter_status, stakeholder_list))
        mysql.connection.commit()
        project_id = cur.lastrowid
        cur.close()
        
        return jsonify({'success': True, 'project_id': project_id})
    except Exception as e:
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/update_project_status', methods=['POST'])
def update_project_status():
    cursor = None
    try:
        project_id = request.form.get('project_id')
        new_status = request.form.get('status')
        
        print(f"DEBUG: Updating project_id={project_id} to status={new_status}")
        
        if not project_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing project ID or status'})
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE projects SET status = %s WHERE project_id = %s AND pm_user_id = %s
        """, (new_status, project_id, session['user_id']))
        
        mysql.connection.commit()
        print(f"DEBUG: Rows affected: {cursor.rowcount}")
        
        if cursor.rowcount > 0:
            cursor.close()
            return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
        else:
            cursor.close()
            return jsonify({'success': False, 'error': 'Project not found or unauthorized'})
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        if cursor:
            cursor.close()
        if mysql.connection:
            mysql.connection.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})

@app.route('/delete_project/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT pm_user_id FROM projects WHERE project_id = %s", (project_id,))
        project = cur.fetchone()
        
        if not project or project['pm_user_id'] != session['user_id']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        cur.execute("DELETE FROM projects WHERE project_id = %s AND pm_user_id = %s", (project_id, session['user_id']))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    except Exception as e:
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# 🔥 PLACEHOLDER ROUTES
@app.route('/pm_projects')
def pm_projects():
    return render_template('dashboards/pm_projects.html')  # Create this later

@app.route('/pm_team')
def pm_team():
    return render_template('dashboards/pm_team.html')  # Create this later

@app.route('/pm_reports')
def pm_reports():
    return render_template('dashboards/pm_reports.html')  # Create this later

# AUTH & UTILITY ROUTES (UNCHANGED)
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, username, email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user:
            send_reset_email(user['user_id'], user['email'], user['username'])
            flash('Reset link sent!', 'success')
            return redirect('/enterprise-login')
        flash('Email not found!', 'error')
    return render_template('auth/forgot_password.html')

def send_reset_email(user_id, email, username):
    try:
        token = RESET_TOKEN_SER.dumps(user_id, salt='password-reset')
        reset_url = f"http://localhost:5000/reset-password/{token}"
        msg = MIMEMultipart()
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = "Risk Sentinel - Password Reset"
        body = f"Hi {username},\n\nClick here to reset: {reset_url}\n\nExpires in 1 hour."
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS: server.starttls()
        if MAIL_USERNAME and MAIL_PASSWORD: server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = RESET_TOKEN_SER.loads(token, salt='password-reset', max_age=3600)
        if request.method == 'POST':
            new_password = request.form.get('password')
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_password, user_id))
            mysql.connection.commit()
            cur.close()
            flash('Password reset successful!', 'success')
            return redirect('/enterprise-login')
        return render_template('auth/reset_password.html', token=token)
    except:
        flash('Invalid/expired link!', 'error')
        return redirect('/enterprise-login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/<role>-dashboard')
@app.route('/<role>-dashboard/tasks')
@app.route('/<role>-dashboard/risks')
@app.route('/<role>-dashboard/reports')
@app.route('/<role>-dashboard/chat')
def universal_dashboard(role):
    if 'user_id' not in session or session.get('role') != role:
        return redirect('/enterprise-login')
    
    context = get_role_data(role)
    context.update({'session': session, 'active_tab': 'overview'})
    
    full_path = request.path
    if '/tasks' in full_path: context['active_tab'] = 'tasks'
    elif '/risks' in full_path: context['active_tab'] = 'risks'
    elif '/reports' in full_path: context['active_tab'] = 'reports'
    elif '/chat' in full_path: context['active_tab'] = 'chat'
    
    template = f"dashboards/pm_dashboard.html" if role == 'pm' else f"dashboards/{ROLE_DASHBOARDS.get(role, 'pm_dashboard.html')}"
    
    try:
        return render_template(template, **context)
    except:
        return f"<h1>{role.title()} Dashboard</h1><p>{context['total_projects']} projects</p><a href='/logout'>Logout</a>"

@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Page Not Found</h1><p><a href='/'>Home</a></p>", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
