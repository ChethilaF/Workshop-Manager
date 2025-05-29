from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# User model for login accounts
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g. 'admin', 'technician'
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Customer model
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    jobs = db.relationship('Job', backref='customer', lazy=True)

# Technician model
class Technician(db.Model):
    __tablename__ = 'technician'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    specialization = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref='technician')


    jobs = db.relationship('Job', backref='technician', lazy=True)

# Job model
class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_registration = db.Column(db.String(20))
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Pending')  # e.g. Pending, In Progress, Completed
    total_cost = db.Column(db.Numeric(10, 2), default=0.00)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    total_work_duration = db.Column(db.Integer, default=0)
    pause_reason = db.Column(db.Text)
    paused_at = db.Column(db.DateTime)
    resume_at = db.Column(db.DateTime)
    accepted = db.Column(db.Boolean, default=False)

class PauseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    paused_at = db.Column(db.DateTime, nullable=False)
    resumed_at = db.Column(db.DateTime)
    reason = db.Column(db.Text)

    job = db.relationship('Job', backref=db.backref('pauses', lazy=True))
