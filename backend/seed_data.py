import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db
from backend.models import User, Enterprise, Vendor, Project, Risk, Task
from datetime import datetime
from werkzeug.security import generate_password_hash

print("🔄 Seeding data (MATCHING YOUR EXISTING SCHEMA)...")

with app.app_context():
    # 1. PM JOHN (MATCHES YOUR DB: id=2, password field)
    pmjohn = User.query.filter_by(username='pm_john').first()
    if not pmjohn:
        pmjohn = User(
            username='pm_john',
            email='pmjohn@remshatech.com',
            password='pass123',  # ← MATCHES YOUR DB 'password' field
            role='PM',
            enterprise_id=1,
            is_active=1
        )
        db.session.add(pmjohn)
        db.session.commit()
        print("✅ Created/Updated PM John")
    
    # 2. ADMIN (MATCHES YOUR DB: id=1)
    admin = User.query.filter_by(username='admin123').first()
    if not admin:
        admin = User(
            username='admin123',
            email='admin@remshatech.com',
            password='pass123',
            role='Admin',
            enterprise_id=1,
            is_active=1
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Created Admin")
    
    # 3. ANALYST (MATCHES YOUR DB: id=4)
    analyst = User.query.filter_by(username='risk_analyst').first()
    if not analyst:
        analyst = User(
            username='risk_analyst',
            email='analyst@remshatech.com', 
            password='pass123',
            role='Analyst',
            enterprise_id=1,
            is_active=1
        )
        db.session.add(analyst)
        db.session.commit()
        print("✅ Created Analyst")
    
    print("🎉 SEEDING COMPLETE!")
    print("👤 LOGIN CREDENTIALS:")
    print("   PM: pm_john / pass123 → http://localhost:5000/enterprise-login")
    print("   Admin: admin123 / pass123")
    print("   Analyst: risk_analyst / pass123")
