# ===== DASHBOARD HELPER FUNCTIONS =====
ENCRYPTED_SMTP_PASS = b'gAAAAAB...'  # Your existing encrypted password
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'risksentinel.help@gmail.com'

def get_breadcrumbs(role, page):
    """Generate breadcrumbs"""
    base = [{'title': 'Home', 'url': '/'}]
    if page == 'dashboard':
        base.append({'title': f'{role.title()} Dashboard', 'url': f'/{role}-dashboard'})
    return base

def get_analyst_dashboard_data(mysql):
    """Analyst analytics data"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as total FROM risks WHERE status != 'Resolved'")
        active_risks = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as high FROM risks WHERE risk_score > 3")
        high_risks = cur.fetchone()['high']
        cur.execute("SELECT rag_status, COUNT(*) as count FROM risks WHERE status != 'Resolved' GROUP BY rag_status")
        rag_data = cur.fetchall()
        cur.close()
        return {'active_risks': active_risks, 'high_risks': high_risks, 'rag_data': rag_data}
    except:
        return {'active_risks': 0, 'high_risks': 0, 'rag_data': []}
