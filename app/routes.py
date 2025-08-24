from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app.models import User
from app.models import Customer, Technician, Job, PauseLog, JobsDone
from app.utils.pdf_generator import generate_job_pdf
from threading import Timer
from flask import session
pause_timers = {}

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("home.html", hide_navbar=True)

@main.route('/login', methods=['GET', 'POST'])
def login():
    return home()

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@main.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@main.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email') or 'Not Provided'
        address = request.form.get('address') or 'Not Provided'

        if not name or not phone:
            flash("Name and phone are required.", "danger")
            return redirect(url_for('main.add_customer'))

        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            address=address
        )

        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully.", "success")
        return redirect(url_for('main.customers'))

    return render_template('add_customer.html')

@main.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        db.session.commit()
        return redirect(url_for('main.customers'))
    return render_template('edit_customer.html', customer=customer)

@main.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('main.customers'))

@main.route('/technicians')
@login_required
def technicians():
    techs = Technician.query.all()
    return render_template('technicians.html', technicians=techs)

@main.route('/add_technician', methods=['GET', 'POST'])
@login_required
def add_technician():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        specialization = request.form.get('specialization')
        role = request.form.get('role')

        if not username or not password or not name:
            flash("Username, password, and name are required.", "danger")
            return redirect(url_for('main.add_technician'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('main.add_technician'))

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        technician = Technician(
            name=name,
            phone=phone,
            specialization=specialization,
            user_id=user.id
        )
        db.session.add(technician)
        db.session.commit()

        flash("Technician account created successfully.", "success")
        return redirect(url_for('main.technicians'))

    return render_template('add_technician.html')

@main.route('/edit_technician/<int:technician_id>', methods=['GET', 'POST'])
@login_required
def edit_technician(technician_id):
    tech = Technician.query.get_or_404(technician_id)
    if request.method == 'POST':
        tech.name = request.form['name']
        tech.email = request.form['email']
        tech.phone = request.form['phone']
        tech.specialization = request.form['specialization']
        db.session.commit()
        return redirect(url_for('main.technicians'))
    return render_template('edit_technician.html', technician=tech)

@main.route('/delete_technician/<int:technician_id>', methods=['POST'])
@login_required
def delete_technician(technician_id):
    tech = Technician.query.get_or_404(technician_id)
    db.session.delete(tech)
    db.session.commit()
    return redirect(url_for('main.technicians'))

@main.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)

@main.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    customers = Customer.query.all()
    technicians = Technician.query.all()

    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

            job = Job(
                description=request.form['description'],
                start_date=start_date,
                end_date=end_date,
                status=request.form['status'],
                target_duration=request.form.get('target_duration', '00:00:00'),
                total_cost=request.form['total_cost'],
                customer_id=request.form['customer_id'],
                technician_id=request.form['technician_id'],
                vehicle_registration=request.form['vehicle_registration']
            )

            db.session.add(job)
            db.session.commit()
            return redirect(url_for('main.jobs'))

        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")

    return render_template('add_job.html', customers=customers, technicians=technicians)

@main.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    customers = Customer.query.all()
    technicians = Technician.query.all()

    if request.method == 'POST':
        job.description = request.form['description']
        job.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        job.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        job.status = request.form['status']
        job.total_cost = float(request.form['total_cost'])
        job.customer_id = int(request.form['customer_id'])
        job.technician_id = int(request.form['technician_id'])
        job.vehicle_registration = request.form['vehicle_registration']

        db.session.commit()
        return redirect(url_for('main.jobs'))

    return render_template('edit_job.html', job=job, customers=customers, technicians=technicians)

@main.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('main.jobs'))

@main.route('/job_control/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_control(job_id):
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'start' and not job.start_time:
            job.start_time = datetime.utcnow()

        elif action == 'pause':
            pause_reason = request.form.get('pause_reason', '')
            pause = PauseLog(
                job_id=job.id,
                paused_at=datetime.utcnow(),
                reason=pause_reason if pause_reason else ""
            )
            db.session.add(pause)
            db.session.commit()

            def auto_resume():
                latest_pause = PauseLog.query.filter_by(
                    job_id=job.id,
                    resumed_at=None
                ).order_by(PauseLog.paused_at.desc()).first()
                if latest_pause and not latest_pause.reason:
                    latest_pause.resumed_at = datetime.utcnow()
                    job.total_work_duration += int(
                        (latest_pause.resumed_at - latest_pause.paused_at).total_seconds()
                    )
                    db.session.commit()

            timer = Timer(300, auto_resume)
            timer.start()
            pause_timers[job_id] = timer

        elif action == 'resume':
            pause = PauseLog.query.filter_by(
                job_id=job.id,
                resumed_at=None
            ).order_by(PauseLog.paused_at.desc()).first()
            if pause:
                pause.resumed_at = datetime.utcnow()
                job.total_work_duration += int(
                    (pause.resumed_at - pause.paused_at).total_seconds()
                )
                if job.id in pause_timers:
                    pause_timers[job.id].cancel()
                    del pause_timers[job.id]
                db.session.commit()

        elif action == 'stop':
            pause = PauseLog.query.filter_by(
                job_id=job.id,
                resumed_at=None
            ).order_by(PauseLog.paused_at.desc()).first()
            if pause:
                pause.resumed_at = datetime.utcnow()
                job.total_work_duration += int(
                    (pause.resumed_at - pause.paused_at).total_seconds()
                )
            job.end_time = datetime.utcnow()
            job.status = "Waiting for Approval"

        db.session.commit()

    # Pass VAPID public key to template for push subscription
    import os
    vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")

    return render_template(
        'job_control.html',
        job=job,
        vapid_public_key=vapid_public_key
    )

@main.route('/jobs/waiting_approval')
@login_required
def jobs_waiting_approval():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    waiting_jobs = Job.query.filter_by(status="Waiting for Approval").all()
    return render_template('waiting_approval.html', jobs=waiting_jobs)

@main.route('/jobs/approve/<int:job_id>', methods=['POST'])
@login_required
def approve_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.status == 'Waiting for Approval':
        job_done = JobsDone(
            job_id=job.id,
            vehicle_registration=job.vehicle_registration,
            description=job.description,
            start_time=job.start_time,
            end_time=job.end_time,
            total_work_duration=job.total_work_duration,
            customer_name=job.customer.name,
            technician_name=job.technician.name,
            pause_summary="\n".join([f"{p.paused_at} - {p.resumed_at or 'Still Paused'}: {p.reason}" for p in job.pauses])
        )
        db.session.add(job_done)
        job.status = 'Completed'
        db.session.commit()
        flash('Job approved and marked as completed.', 'success')

    return redirect(url_for('main.jobs_waiting_approval'))

@main.route('/jobs/retry/<int:job_id>', methods=['POST'])
@login_required
def retry_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.status == 'Waiting for Approval':
        job.status = 'Declined at Approval'
        db.session.commit()
        flash('Job returned to technician for review.', 'warning')

    return redirect(url_for('main.jobs_waiting_approval'))

@main.route('/job_pdf/<int:job_id>')
@login_required
def record_job_done(job):
    from app.models import JobsDone
    job = Job.query.get_or_404(job_id)
    job_done = JobsDone(
        job_id=job.id,
        customer_name=job.customer.name,
        technician_name=job.technician.name,
        vehicle_registration=job.vehicle_registration,
        start_time=job.start_time,
        end_time=job.end_time,
        total_work_duration=job.total_work_duration,
        description=job.description
    )
    db.session.add(job_done)
    db.session.commit()

@main.route('/job_complete/<int:job_id>')
@login_required
def job_complete(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_complete.html', job=job)

@main.route('/staff')
@login_required
def staff_dashboard():
    techs = Technician.query.all()
    return render_template('staff_dashboard.html', techs=techs)

@main.route('/staff_jobs/<int:tech_id>')
@login_required
def staff_jobs(tech_id):
    technician = Technician.query.get_or_404(tech_id)
    jobs = Job.query.filter_by(technician_id=technician.id).all()
    return render_template('staff_jobs.html', technician=technician, jobs=jobs)

@main.route('/accept_job/<int:job_id>', methods=['POST'])
@login_required
def accept_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.accepted = True
    db.session.commit()
    return redirect(url_for('main.staff_dashboard'))

@main.route('/log_shift/<int:tech_id>', methods=['GET', 'POST'])
def log_shift(tech_id):
    technician = Technician.query.get_or_404(tech_id)
    today = date.today()
    shift = ShiftLog.query.filter_by(technician_id=tech_id, date=today).first()

    if request.method == 'POST':
        if not shift:
            start = request.form.get('start_time')
            if not start:
                flash("Start time is required.", "danger")
                return redirect(request.url)
            try:
                start_time = datetime.strptime(start, '%H:%M').time()
            except ValueError:
                flash("Invalid start time format.", "danger")
                return redirect(request.url)

            shift = ShiftLog(
                technician_id=tech_id,
                date=today,
                start_time=start_time
            )
            db.session.add(shift)
            db.session.commit()
            flash("Start time logged.", "success")

        elif shift and not shift.end_time:
            end = request.form.get('end_time')
            if not end:
                flash("End time is required.", "danger")
                return redirect(request.url)
            try:
                end_time = datetime.strptime(end, '%H:%M').time()
            except ValueError:
                flash("Invalid end time format.", "danger")
                return redirect(request.url)

            shift.end_time = end_time
            db.session.commit()
            flash("End time logged.", "success")

        return redirect(url_for('main.staff_dashboard'))

    return render_template('log_shift.html', technician=technician, shift=shift)

@main.route('/generate_weekly_summary/<int:tech_id>')
@login_required
def generate_weekly_summary(tech_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    filename = generate_weekly_summary_pdf(tech_id)
    if filename:
        flash("Weekly summary PDF generated.", "success")
        return send_from_directory('app/static/pdfs', filename, as_attachment=True)
    else:
        flash("Could not generate PDF.", "danger")
        return redirect(url_for('main.staff_dashboard'))

@main.route('/download_pdf/<filename>')
@login_required
def download_pdf(filename):
    return send_from_directory('app/static/pdfs', filename, as_attachment=True)



# Notification system
import os
import json
from app.models import PushSubscription
from pywebpush import webpush, WebPushException

@main.route('/save-subscription', methods=['POST'])
@login_required
def save_subscription():
    if current_user.role != 'technician':
        return {"error": "Only technicians can subscribe"}, 403

    data = request.get_json()
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh')
    auth_key = keys.get('auth')

    # Avoid duplicates
    existing = PushSubscription.query.filter_by(
        technician_id=current_user.id,
        endpoint=endpoint
    ).first()

    if not existing:
        sub = PushSubscription(
            technician_id=current_user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth_key
        )
        db.session.add(sub)
        db.session.commit()

    return {"status": "Subscription saved"}
