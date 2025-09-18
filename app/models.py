from app import db
from flask_login import UserMixin
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================
# User Model
# ==========================
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='technician')  # roles: admin, technician, finance, reception
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Password hashing methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Relationship with Technician (if user is technician)
    technician = db.relationship('Technician', backref='user', uselist=False)

    def __repr__(self):
        return f"<User {self.username} - Role: {self.role}>"

# ==========================
# Technician Model
# ==========================
class Technician(db.Model):
    __tablename__ = 'technician'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # link to User table
    jobs = db.relationship('Job', backref='technician', lazy=True)

    def __repr__(self):
        return f"<Technician {self.full_name}>"

# ==========================
# Customer Model
# ==========================
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    vehicle_reg = db.Column(db.String(50), nullable=False)
    jobs = db.relationship('Job', backref='customer', lazy=True)

    def __repr__(self):
        return f"<Customer {self.full_name} - {self.vehicle_reg}>"

# ==========================
# Job Model
# ==========================
class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, in_progress, paused, completed
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    pause_logs = db.relationship('PauseLog', backref='job', lazy=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def total_worked_time(self):
        """
        Calculate total time worked on job excluding pauses.
        Returns timedelta.
        """
        if not self.start_time or not self.end_time:
            return None

        total_pause = sum((pause.duration() for pause in self.pause_logs if pause.duration()), datetime.min - datetime.min)
        total_time = self.end_time - self.start_time - total_pause
        return total_time

    def __repr__(self):
        return f"<Job {self.title} - Status: {self.status}>"

# ==========================
# Pause Log Model
# ==========================
class PauseLog(db.Model):
    __tablename__ = 'pause_log'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    pause_start = db.Column(db.DateTime, default=datetime.utcnow)
    pause_end = db.Column(db.DateTime)

    def duration(self):
        if self.pause_end:
            return self.pause_end - self.pause_start
        return None

    def __repr__(self):
        return f"<PauseLog Job {self.job_id} - {self.pause_start} to {self.pause_end}>"

# ==========================
# Shift Model (optional)
# ==========================
class Shift(db.Model):
    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def __repr__(self):
        return f"<Shift Technician {self.technician_id} - {self.start_time} to {self.end_time}>"

# ==========================
# Notification Model (optional)
# ==========================
class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(150))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f"<Notification {self.title} - Read: {self.is_read}>"
