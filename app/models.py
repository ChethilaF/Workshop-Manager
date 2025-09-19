from app import db
from flask_login import UserMixin
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='technician')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} - Role: {self.role}>"


# ==========================
# Technician Model
# ==========================
class Technician(db.Model):
    __tablename__ = 'technicians'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    specialization = db.Column(db.String(120))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref=db.backref('technician',
                           uselist=False))
    jobs = db.relationship('Job', back_populates='technician')


# ==========================
# Customer Model
# ==========================
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))

    jobs = db.relationship('Job', back_populates='customer')

    def __repr__(self):
        return f"<Customer {self.full_name}>"


# ==========================
# Job Model
# ==========================
class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    job_description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')

    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'),
                              nullable=True)
    technician = db.relationship('Technician', back_populates='jobs')

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = db.relationship('Customer', back_populates='jobs')

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    target_duration = db.Column(db.Integer, default=0)  # minutes
    total_work_duration = db.Column(db.Integer, default=0)  # minutes
    vehicle_registration = db.Column(db.String(50))
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_year = db.Column(db.Integer)
    vehicle_color = db.Column(db.String(50))
    total_cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    pause_logs = db.relationship('PauseLog', backref='job', lazy=True)

    def __repr__(self):
        return f"<Job {self.job_description} - Status: {self.status}>"


# ==========================
# Pause Log Model
# ==========================
class PauseLog(db.Model):
    __tablename__ = 'pause_log'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    pause_start = db.Column(db.DateTime, default=datetime.utcnow)
    pause_end = db.Column(db.DateTime)
    reason = db.Column(db.String(255))

    def duration(self):
        if self.pause_end:
            return (self.pause_end - self.pause_start).total_seconds()
        return 0


# ==========================
# Shift Model
# ==========================
class Shift(db.Model):
    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None


# ==========================
# Notification Model
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


# ==========================
# Push Subscription Model
# ==========================
class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='push_subscriptions')
