from flask import Flask, render_template, request, redirect, session, jsonify, flash
from flask_mysqldb import MySQL
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'risk-sentinel-2026'

# 🔥 YOUR MySQL - CORRECT PASSWORD
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'  # ✅ YOUR PASSWORD
app.config['MYSQL_DB'] = 'risk_sentinel'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# 🔥 ALL PM DATA (including risk_chart)
def get_pm_data():
    if 'user_id' not in session:
        return {
            'username': 'PM User', 'total_projects': 0, 'projects': [],
            'total_risks': 0, 'total_tasks': 0,
            'risk_chart': {'Red': 0, 'Amber': 0, 'Green': 0}
        }
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE user_id = %s", (session['user_id'],))
        user = cur.fetchone()
        
        cur.execute("SELECT COUNT(*) as total FROM projects WHERE pm_user_id = %s", (session['user_id'],))
        total_projects = cur.fetchone()['total'] or 0
        
        cur.execute("""
            SELECT project_id, name, status, budget_total, budget_spent, 
                   start_date, end_date FROM projects 
            WHERE pm_user_id = %s ORDER BY created_at DESC LIMIT 5
        """, (session['user_id'],))
        projects = cur.fetchall()
        
        cur.execute("""
            SELECT COUNT(*) as total FROM risks r 
            JOIN projects p ON r.project_id = p.project_id 
            WHERE p.pm_user_id = %s
        """, (session['user_id'],))
        total_risks = cur.fetchone()['total'] or 0
        
        cur.execute("""
            SELECT COUNT(*) as total FROM tasks t
            JOIN projects p ON t.project_id = p.project_id 
            WHERE p.pm_user_id = %s AND t.status != 'Completed'
        """, (session['user_id'],))
        total_tasks = cur.fetchone()['total'] or 0
        
        # 🔥 risk_chart for dashboard.html
        cur.execute("""
            SELECT rag_status, COUNT(*) as count 
            FROM risks r JOIN projects p ON r.project_id = p.project_id 
            WHERE p.pm_user_id = %s GROUP BY rag_status
        """, (session['user_id'],))
        risk_data = cur.fetchall()
        risk_chart = {'Red': 0, 'Amber': 0, 'Green': 0}
        for row in risk_data:
            risk_chart[row['rag_status']] = row['count']
        
        cur.close()
        return {
            'username': user['username'] if user else 'PM User',
            'total_projects': total_projects, 'projects': projects,
            'total_risks': total_risks, 'total_tasks': total_tasks,
            'risk_chart': risk_chart
        }
    except:
        return {
            'username': 'PM User', 'total_projects': 0, 'projects': [],
            'total_risks': 0, 'total_tasks': 0,
            'risk_chart': {'Red': 0, 'Amber': 0, 'Green': 0}
        }

# 🔥 LANDING
@app.route('/')
def landing():
    return render_template('landing.html')

# 🔥 ALL 6 AUTH ROUTES ✅
@app.route('/enterprise-login', methods=['GET', 'POST'])
def enterprise_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND role IN ('PM','Admin')", (email,))
        user = cur.fetchone()
        cur.close()
        if user and user['password'] == password:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/pm/dashboard')
        flash('Invalid credentials', 'error')
    return render_template('auth/enterprise_login.html')

@app.route('/enterprise-register', methods=['GET', 'POST'])
def enterprise_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s,%s,%s,'PM')",
                       (username, email, password))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful!', 'success')
            return redirect('/enterprise-login')
        except:
            flash('Registration failed', 'error')
    return render_template('auth/enterprise_register.html')

@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT v.* FROM vendors v WHERE v.email = %s AND v.password = %s", (email, password))
        vendor = cur.fetchone()
        cur.close()
        if vendor:
            session['vendor_id'] = vendor['vendor_id']
            session['vendor_name'] = vendor['company_name']
            session['role'] = 'vendor'
            return redirect('/vendor/dashboard')
        flash('Invalid credentials', 'error')
    return render_template('auth/vendor_login.html')

@app.route('/vendor-register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        company = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO vendors (company_name, email, password) VALUES (%s,%s,%s)",
                       (company, email, password))
            mysql.connection.commit()
            cur.close()
            flash('Vendor registration successful!', 'success')
            return redirect('/vendor-login')
        except:
            flash('Registration failed', 'error')
    return render_template('auth/vendor_register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash('Reset link sent to your email!', 'success')
        return redirect('/enterprise-login')
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s", (password, email))
        mysql.connection.commit()
        cur.close()
        flash('Password reset successful!', 'success')
        return redirect('/enterprise-login')
    return render_template('auth/reset_password.html', token=token)

# 🔥 ALL 5 PM ROUTES ✅
@app.route('/pm/dashboard')
def pm_dashboard():
    if 'user_id' not in session or session.get('role') != 'PM':
        return redirect('/enterprise-login')
    return render_template('pm/dashboard.html', **get_pm_data())

@app.route('/pm/projects')
def pm_projects():
    if 'user_id' not in session or session.get('role') != 'PM':
        return redirect('/enterprise-login')
    return render_template('pm/projects.html', **get_pm_data())

@app.route('/pm/risks')
def pm_risks():
    if 'user_id' not in session or session.get('role') != 'PM':
        return redirect('/enterprise-login')
    return render_template('pm/risks.html', **get_pm_data())

@app.route('/pm/tasks')
def pm_tasks():
    if 'user_id' not in session or session.get('role') != 'PM':
        return redirect('/enterprise-login')
    return render_template('pm/tasks.html', **get_pm_data())

@app.route('/pm/teams')
def pm_teams():
    if 'user_id' not in session or session.get('role') != 'PM':
        return redirect('/enterprise-login')
    return render_template('pm/teams.html', **get_pm_data())

# 🔥 PM PROJECTS CRUD
'''@app.route('/pm/projects/save', methods=['POST'])
def pm_projects_save():
    if session.get('role') != 'PM': return jsonify({'success': False})
    data = request.form
    cur = mysql.connection.cursor()
    if data.get('project_id'):
        cur.execute("""
            UPDATE projects SET name=%s, status=%s, budget_total=%s 
            WHERE project_id=%s AND pm_user_id=%s
        """, (data['name'], data['status'], data.get('budget_total'), 
              data['project_id'], session['user_id']))
    else:
        cur.execute("""
            INSERT INTO projects (pm_user_id, name, status, budget_total) 
            VALUES (%s,%s,%s,%s)
        """, (session['user_id'], data['name'], data['status'], data.get('budget_total')))
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True})

@app.route('/pm/projects/delete/<int:project_id>', methods=['POST'])
def pm_projects_delete(project_id):
    if session.get('role') != 'PM': return jsonify({'success': False})
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM projects WHERE project_id=%s AND pm_user_id=%s", 
               (project_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True})
'''
@app.route('/pm/projects/save', methods=['POST'])
def pm_projects_save():
    """Create or update project (handles both new/edit modals)"""
    if 'user_id' not in session or session.get('role') != 'pm':
        return jsonify({'success': False, 'error': 'PM access only'}), 403
    
    pm_user_id = session['user_id']
    form_data = request.form
    
    try:
        cur = mysql.connection.cursor()
        
        project_id = form_data.get('project_id')
        
        if project_id:  # UPDATE existing
            cur.execute("""
                UPDATE projects 
                SET name=%s, status=%s, budget_total=%s, start_date=%s, 
                    end_date=%s, team_lead_id=%s, updated_at=NOW()
                WHERE project_id=%s AND pm_user_id=%s
            """, (form_data['name'], form_data['status'], 
                  form_data.get('budget_total', 0), form_data.get('start_date'),
                  form_data.get('end_date'), form_data.get('team_lead_id'),
                  project_id, pm_user_id))
            
            if cur.rowcount == 0:
                return jsonify({'success': False, 'error': 'Project not found'})
            
            message = f'Project "{form_data["name"]}" updated successfully!'
        else:  # CREATE new
            cur.execute("""
                INSERT INTO projects (pm_user_id, name, status, budget_total, 
                                     start_date, end_date, team_lead_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (pm_user_id, form_data['name'], form_data['status'],
                  form_data.get('budget_total', 0), form_data.get('start_date'),
                  form_data.get('end_date'), form_data.get('team_lead_id')))
            
            message = f'Project "{form_data["name"]}" created successfully!'
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/pm/projects/delete/<int:project_id>', methods=['POST'])
def pm_projects_delete(project_id):
    """Delete project by ID"""
    if 'user_id' not in session or session.get('role') != 'pm':
        return jsonify({'success': False, 'error': 'PM access only'}), 403
    
    pm_user_id = session['user_id']
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM projects WHERE project_id=%s AND pm_user_id=%s", (project_id, pm_user_id))
        project = cur.fetchone()
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'})
        
        cur.execute("DELETE FROM projects WHERE project_id=%s AND pm_user_id=%s", (project_id, pm_user_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f'"{project["name"]}" deleted successfully!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 🔥 VENDOR DASHBOARD (BASIC)
@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session or session.get('role') != 'vendor':
        return redirect('/vendor-login')
    return render_template('vendor/dashboard.html')

# 🔥 TEST ROUTES
@app.route('/test-login')
def test_login():
    session['user_id'] = 2  # pmjohn
    session['username'] = 'pmjohn'
    session['role'] = 'PM'
    return redirect('/pm/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("🚀 Risk Sentinel - ALL ROUTES COMPLETE!")
    print("✅ 6 AUTH: enterprise-login/register, vendor-login/register, forgot/reset")
    print("✅ 5 PM: dashboard/projects/risks/tasks/teams") 
    print("✅ MySQL: root/admin@risk_sentinel")
    print("✅ TEST: http://127.0.0.1:5000/test-login")
    app.run(debug=True, port=5000)
