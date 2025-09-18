from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.utils.pdf_generator import get_pdfs_for_tech
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


def create_app():

    app = Flask(__name__)

    # App configuration
    app.config['SECRET_KEY'] = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Workshop.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Disable unnecessary tracking

    # VAPID keys for push notifications
    app.config["VAPID_PUBLIC_KEY"] = os.getenv("VAPID_PUBLIC_KEY") or ""
    app.config["VAPID_PRIVATE_KEY"] = os.getenv("VAPID_PRIVATE_KEY") or ""

    # Initialize extensions with this app
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Import and register routes blueprint
        from .routes import main
        app.register_blueprint(main)

        # Import notification function and Job model
        from app.utils.notifications import send_push_to_technician
        from app.models import Job

        # Function to notify technicians about active jobs every hour
        def notify_active_jobs():
            active_jobs = Job.query.filter(Job.status == "In Progress").all()
            for job in active_jobs:
                send_push_to_technician(
                    job.technician_id,
                    "Job Reminder",
                    f"You have an active job: {job.description}",
                    url=f"/job_control/{job.id}"
                )

        scheduler = BackgroundScheduler()
        scheduler.add_job(func=notify_active_jobs, trigger="interval", hours=1)
        scheduler.start()

    app.jinja_env.globals.update(get_pdfs_for_tech=get_pdfs_for_tech)

    return app
