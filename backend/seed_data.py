import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db
from backend.models import User, Enterprise, Vendor, Project, Risk, Task
from datetime import datetime

print("🔄 Seeding data (keeping existing tables)...")

with app.app_context():
    # DON'T drop_all() - causes circular dependency
    
    # 1. PM JOHN
    pmjohn = User.query.filter_by(username='pmjohn').first()
    if not pmjohn:
        pmjohn = User(username='pmjohn', email='pmjohn@test.com', password='pass12345', role='PM')
        db.session.add(pmjohn)
        db.session.commit()
        print("✅ Created PM John")
    
    # 2. ENTERPRISE
    enterprise = Enterprise.query.filter_by(name='TechCorp Inc.').first()
    if not enterprise:
        enterprise = Enterprise(name='TechCorp Inc.')
        db.session.add(enterprise)
        db.session.commit()
        print("✅ Created Enterprise")
    
    # 3. PROJECTS
    project_count = Project.query.count()
    if project_count == 0:
        projects = [
            Project(name='Alpha Sprint', enterprise_id=enterprise.enterprise_id),
            Project(name='Beta Release', enterprise_id=enterprise.enterprise_id),
            Project(name='Gamma MVP', enterprise_id=enterprise.enterprise_id)
        ]
        for project in projects:
            db.session.add(project)
        db.session.commit()
        print("✅ Created 3 Projects")
    
    # 4. RISKS (only if none exist)
    risk_count = Risk.query.count()
    if risk_count == 0:
        risks = [
            Risk(title='Server Overload', risk_score=4.5, status='Open'),
            Risk(title='Database Timeout', risk_score=3.8, status='Open'),
            Risk(title='Vendor Delay', risk_score=2.9, status='Open')
        ]
        for risk in risks:
            db.session.add(risk)
        db.session.commit()
        print("✅ Created 3 Risks")
    
    print("🎉 SEEDING COMPLETE!")
    print("👤 LOGIN: pmjohn / pass12345")
    print("🌐 http://localhost:5000/enterprise-login")
