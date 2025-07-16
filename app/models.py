from app import db
from flask_login import UserMixin
from app import login_manager
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), default='Not Provided')
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), default='Not Provided')


class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    specialization = db.Column(db.String(100))
    user_id = db.Column(db.Integer, unique=True, nullable=False)

class Job(db.Model):
    tablename = 'job'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_registration = db.Column(db.String(20))
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Pending')
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))