from app import db
from flask_login import UserMixin
from app import login_manager
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    vehicle_registration = db.Column(db.String(20))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Pending')
    total_cost = db.Column(db.Numeric(10, 2), default=0.00)
    total_work_duration = db.Column(db.Integer, default=0)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=False)

class PauseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    paused_at = db.Column(db.DateTime, nullable=False)
    resumed_at = db.Column(db.DateTime)
    reason = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))