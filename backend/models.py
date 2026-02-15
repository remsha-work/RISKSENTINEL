from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Risk(db.Model):
    __tablename__ = 'risks'
    risk_id = db.Column(db.Integer, primary_key=True)
    risk_title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(20))  # High/Medium/Low
    status = db.Column(db.String(20))    # Open/Closed/In Progress
    risk_category = db.Column(db.String(50))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    assigned_to = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    
    # Relationship
    project = db.relationship('Project', backref='risks')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Planning')
    budget_total = db.Column(db.Float, default=0.0)
    pm_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.project_name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    pm_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.task_name}>'

