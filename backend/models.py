from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ========== USERS ==========
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.Enum('Admin','PM','Analyst','TL','SeniorDev','JuniorDev'), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    enterprise_id = db.Column(db.Integer, db.ForeignKey('enterprises.enterprise_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ✅ NO relationships - prevents ambiguous foreign keys

# ========== ENTERPRISES ==========
class Enterprise(db.Model):
    __tablename__ = 'enterprises'
    enterprise_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    pm_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ✅ NO backref relationships

# ========== VENDORS ==========
class Vendor(db.Model):
    __tablename__ = 'vendors'
    vendor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    risk_score = db.Column(db.Float, default=0.00)
    status = db.Column(db.Enum('Active','Inactive'), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== PROJECTS ==========
class Project(db.Model):
    __tablename__ = 'projects'
    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    enterprise_id = db.Column(db.Integer, db.ForeignKey('enterprises.enterprise_id'))
    pm_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    team_lead_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    status = db.Column(db.Enum('Planning','Active','OnHold','Completed'), default='Planning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    budget_total = db.Column(db.Float)
    budget_spent = db.Column(db.Float, default=0.00)
    description = db.Column(db.Text)
    charter_status = db.Column(db.Enum('Draft','Approved','Active','Completed'), default='Draft')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    stakeholder_list = db.Column(db.Text)

# ========== PROJECT HEALTH ==========
class ProjectHealth(db.Model):
    __tablename__ = 'project_health'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    health_score = db.Column(db.Enum('Red','Yellow','Green'))
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== RISK TYPES ==========
class RiskType(db.Model):
    __tablename__ = 'risk_types'
    type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.Enum('Technical','Non-Tech','External'), nullable=False)
    description = db.Column(db.Text)

# ========== RISKS ==========
class Risk(db.Model):
    __tablename__ = 'risks'
    risk_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_type_id = db.Column(db.Integer, db.ForeignKey('risk_types.type_id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    probability = db.Column(db.Float)
    impact_score = db.Column(db.Integer)
    risk_score = db.Column(db.Float)
    health_impact = db.Column(db.Enum('Red','Yellow','Green'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    tracker_id = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.vendor_id'))
    status = db.Column(db.Enum('Identified','Open','InProgress','Mitigated','Closed'), default='Identified')
    progress = db.Column(db.Integer, default=0)
    mitigation_progress = db.Column(db.Integer, default=0)
    vendor_status = db.Column(db.Enum('pending','submitted','approved'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    risk_category = db.Column(db.Enum('Testing','Finance','Technical','Vendor','Compliance','Operational'), default='Operational')
    test_type = db.Column(db.Enum('Unit','Integration','Performance','Regression'))
    finance_impact = db.Column(db.Float, default=0.00)
    rag_status = db.Column(db.Enum('Red','Amber','Green'), default='Amber')
    project_blocker = db.Column(db.Boolean, default=False)
    flagged_by = db.Column(db.Integer)
    comments = db.Column(db.Text)
    milestone_delay_days = db.Column(db.Integer, default=0)

# ========== TASKS ==========
class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('NotStarted','InProgress','Testing','Completed'), default='NotStarted')
    priority = db.Column(db.Enum('High','Medium','Low'), default='Medium')
    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== MILESTONES ==========
class Milestone(db.Model):
    __tablename__ = 'milestones'
    milestone_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    title = db.Column(db.String(255), nullable=False)
    target_date = db.Column(db.Date)
    status = db.Column(db.Enum('Pending','InProgress','Completed','Delayed'), default='Pending')
    completed_date = db.Column(db.Date)

# ========== CHAT ==========
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.room_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
