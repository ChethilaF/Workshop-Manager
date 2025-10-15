from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, send_from_directory, jsonify, abort)
from app.models import (User, Customer, Technician, Shift, Job, PauseLog,
                        PushSubscription, Notification)
from flask_login import login_user, logout_user, login_required, current_user
# werkzeug security for password hashing and verification,
#  used to hash the passwords entered by the admin when registering a new user
#  and when the user is  login in it is used to verify them during login.
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timedelta
from app.utils.pdf_generator import (generate_weekly_summary_pdf,
                                     get_pdfs_for_tech, PDF_DIR)
from app import db
from flask import current_app
# os import for file path handling
import os

# Dictionary to track pause timers for jobs
pause_timers = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Blueprint for main routes
main = Blueprint('main', __name__)


# ------------------- AUTHENTICATION -------------------

# Home and login route combined
@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password_hash,
                                        request.form["password"]):
            login_user(user)

            # Redirect based on role
            if user.role == 'reception':
                return redirect(url_for('main.shift_dashboard'))
            elif user.role == "admin":
                return redirect(url_for("main.admin_dashboard"))
            elif user.role == "technician":
                return redirect(url_for("main.staff_dashboard"))
            else:
                flash("Unknown role assigned.", "error")
                return redirect(url_for("main.home"))

        flash("Invalid credentials", "error")

    return render_template("home.html", hide_navbar=True)


# Redirect /login to home for simplicity
@main.route('/login', methods=['GET', 'POST'])
def login():
    return home()


# Logout route
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


# ------------------- DASHBOARDS -------------------


# Admin dashboard showing all admin actions.
@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.staff_dashboard'))

    technicians = Technician.query.all()
    pending_jobs = Job.query.filter_by(accepted=None).all()
    accepted_jobs = Job.query.filter_by(accepted=True).all()
    declined_jobs = Job.query.filter_by(accepted=False).all()

    return render_template('admin_dashboard.html',
                           technicians=technicians,
                           pending_jobs=pending_jobs,
                           accepted_jobs=accepted_jobs,
                           declined_jobs=declined_jobs)


# Staff dashboard showing technicians.
@main.route('/staff')
@login_required
def staff_dashboard():
    if current_user.role not in ["technician", "admin"]:
        flash("Access denied. Technicians only.", "error")
        return redirect(url_for("main.admin_dashboard"))
    elif current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    VAPID_PUBLIC_KEY = current_app.config.get("VAPID_PUBLIC_KEY")
    techs = Technician.query.all()
    return render_template("staff_dashboard.html", techs=techs,
                           vapid_public_key=VAPID_PUBLIC_KEY)


# Shift dashboard for reception users.
@main.route('/shift_dashboard')
@login_required
def shift_dashboard():
    if current_user.role != "reception":
        flash("Access denied.", "error")
        return redirect(url_for('main.staff_dashboard'))

    techs = Technician.query.all()
    return render_template('shift_dashboard.html', techs=techs)


# ------------------- CUSTOMER MANAGEMENT -------------------


# List all customers
@main.route('/customers')
@login_required
def customers():
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


@main.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        # Validate required fields
        if not full_name or not phone:
            flash('Full Name and Phone are required', 'danger')
            return redirect(url_for('main.add_customer'))

        # Create and add the customer
        new_customer = Customer(
            full_name=full_name,
            phone=phone,
            email=email
        )
        db.session.add(new_customer)
        db.session.commit()
        flash(f'Customer "{full_name}" added successfully!', 'success')
        return redirect(url_for('main.customers'))

    return render_template('add_customer.html')


# ==========================
# Edit Customer Route
# ==========================
@main.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not full_name or not phone:
            flash('Full Name and Phone are required', 'danger')
            return redirect(url_for('main.edit_customer',
                            customer_id=customer_id))

        # Update customer
        customer.full_name = full_name
        customer.phone = phone
        customer.email = email

        db.session.commit()
        flash(f'Customer "{full_name}" updated successfully!', 'success')
        return redirect(url_for('main.customers'))

    return render_template('edit_customer.html', customer=customer)


@main.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('main.customers'))


# ------------------- TECHNICIAN MANAGEMENT -------------------
# -------------------------
# List all technicians
# -------------------------
@main.route('/technicians')
@login_required
def technicians():
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    technicians = Technician.query.all()
    return render_template('technicians.html', technicians=technicians)


# -------------------------
# Add a new technician
# -------------------------
@main.route('/add_technician', methods=['GET', 'POST'])
@login_required
def add_technician():
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        specialization = request.form.get('specialization')
        role = request.form.get('role')

        if not username or not password or not role or not name:
            flash("All required fields must be filled.", "warning")
            return redirect(url_for('main.add_technician'))

        if not email:
            email = 'Not Provided'

        try:
            # Create the User first
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()

            # Create the Technician linked to the User
            new_technician = Technician(
                name=name,
                phone=phone,
                specialization=specialization,
                user_id=new_user.id
            )
            db.session.add(new_technician)
            db.session.commit()

            flash("Technician added successfully.", "success")
            return redirect(url_for('main.technicians'))

        except IntegrityError as e:
            db.session.rollback()
            if "user.username" in str(e.orig):
                flash("Username already exists. Please choose another.",
                      "error")
            elif "user.email" in str(e.orig):
                flash("Email already exists. Please choose another.", "error")
            else:
                flash(f"Error adding technician: {str(e)}", "error")
            return redirect(url_for('main.add_technician'))

    return render_template('add_technician.html')


# -------------------------
# Edit technician
# -------------------------
@main.route('/edit_technician/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_technician(id):
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    tech = Technician.query.get_or_404(id)

    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('password')
        email = request.form.get('email')
        tech.user.email = email.strip() if email and email.strip() else None
        name = request.form.get('name')
        phone = request.form.get('phone')
        specialization = request.form.get('specialization')
        role = request.form.get('role')

        # Update user info
        tech.user.username = username
        tech.user.role = role
        tech.user.email = email.strip() if email and email.strip() else None

        if new_password:
            tech.user.set_password(new_password)

        # Update technician info
        tech.name = name
        tech.phone = phone
        tech.specialization = specialization

        try:
            db.session.commit()
            flash("Technician updated successfully.", "success")
        except IntegrityError as e:
            db.session.rollback()
            if "user.username" in str(e.orig):
                flash("Username already exists. Please choose another.",
                      "error")
            elif "user.email" in str(e.orig):
                flash("Email already exists. Please choose another.", "error")
            else:
                flash("Error updating technician.", "error")

        return redirect(url_for('main.technicians'))

    return render_template('edit_technician.html', technician=tech)


# -------------------------
# Delete technician
# -------------------------
@main.route('/delete_technician/<int:id>', methods=['POST'])
@login_required
def delete_technician(id):
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    tech = Technician.query.get_or_404(id)
    user = tech.user

    if user:
        db.session.delete(user)
    else:
        db.session.delete(tech)

    db.session.commit()
    flash("Technician deleted successfully.", "success")
    return redirect(url_for('main.technicians'))


# ------------------- JOB MANAGEMENT -------------------
# List all jobs
@main.route('/jobs')
@login_required
def jobs():
    """List all jobs."""
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)


@main.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    customers = Customer.query.all()
    technicians = Technician.query.all()

    if request.method == 'POST':
        # Get form data
        job_description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        target_days = int(request.form.get('target_days', 0))
        target_hours = int(request.form.get('target_hours', 0))
        target_minutes = int(request.form.get('target_minutes', 0))
        status = request.form.get('status')
        customer_id = request.form.get('customer_id')
        technician_id = request.form.get('technician_id')

        # Required check
        if not job_description or not customer_id or not technician_id:
            flash("Job description, customer, and technician are required.",
                  "warning")
            return redirect(url_for('main.add_job'))

        # Convert dates
        start_time = datetime.strptime(start_date_str,
                                       '%Y-%m-%d') if start_date_str else None
        end_time = datetime.strptime(end_date_str,
                                     '%Y-%m-%d') if end_date_str else None

        # Total duration in minutes
        total_duration = target_days*24*60 + target_hours*60 + target_minutes

        technician_id = request.form.get('technician_id')

        new_job = Job(
            job_description=job_description,
            start_time=start_time,
            end_time=end_time,
            target_duration=total_duration,
            status=status or 'Pending',
            customer_id=customer_id,
            technician_id=technician_id,  # <-- correct column
            vehicle_registration=request.form.get('vehicle_registration'),
            vehicle_make=request.form.get('vehicle_make'),
            vehicle_model=request.form.get('vehicle_model'),
            vehicle_year=request.form.get('vehicle_year'),
            vehicle_color=request.form.get('vehicle_color'),
            total_cost=request.form.get('total_cost') or 0.0,
            notes=request.form.get('notes')
        )

        db.session.add(new_job)
        db.session.commit()
        flash("Job added successfully.", "success")
        return redirect(url_for('main.jobs'))

    return render_template('add_job.html', customers=customers,
                           technicians=technicians)


@main.route('/edit_job/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    job = Job.query.get_or_404(id)
    customers = Customer.query.all()
    technicians = Technician.query.all()

    if request.method == 'POST':
        job.job_description = request.form.get('description')
        job.customer_id = request.form.get('customer_id')
        job.assigned_technician_id = request.form.get('technician_id')
        job.status = request.form.get('status')

        # Dates
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        job.start_time = (datetime.strptime(start_date_str, '%Y-%m-%d')
                          if start_date_str else None)
        job.end_time = (datetime.strptime(end_date_str, '%Y-%m-%d')
                        if end_date_str else None)

        # Target duration
        target_days = int(request.form.get('target_days', 0))
        target_hours = int(request.form.get('target_hours', 0))
        target_minutes = int(request.form.get('target_minutes', 0))
        job.target_duration = (target_days*24*60 +
                               target_hours*60 + target_minutes)

        db.session.commit()
        flash("Job updated successfully.", "success")
        return redirect(url_for('main.jobs'))

    # Precompute days, hours, minutes for dropdowns
    total_minutes = job.target_duration or 0
    target_days = total_minutes // (24*60)
    target_hours = (total_minutes % (24*60)) // 60
    target_minutes = total_minutes % 60

    return render_template(
        'edit_job.html',
        job=job,
        customers=customers,
        technicians=technicians,
        target_days=target_days,
        target_hours=target_hours,
        target_minutes=target_minutes
    )


# Delete a job
@main.route('/delete_job/<int:id>', methods=['POST'])
@login_required
def delete_job(id):
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully.", "success")
    return redirect(url_for('main.jobs'))


# ------------------- JOB CONTROL (Technician actions) -------------------

# View and manage a specific job
@main.route('/job_control/<int:job_id>')
@login_required
def job_control(job_id):
    job = Job.query.get_or_404(job_id)
    if (
        current_user.role == 'technician'
        and job.technician.user_id != current_user.id
    ):
        flash("Unauthorized action.", "error")
        return redirect(url_for('main.staff_dashboard'))
    return render_template('job_control.html', job=job)


# Accept a job
@main.route('/accept_job/<int:job_id>', methods=['POST'])
@login_required
def accept_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Only the assigned technician or admin can accept
    if (
        current_user.role == 'technician'
        and job.technician.user_id != current_user.id
    ):
        flash("Unauthorized action.", "error")
        return redirect(url_for('main.staff_dashboard'))

    # Update job status
    job.accepted = True
    job.status = "Accepted"

    # Create admin notifications
    technician_name = (job.technician.name if
                       job.technician else "Unknown Technician")
    message = (
        f"{technician_name} has accepted the job of "
        f"{job.vehicle_color or 'N/A'} - {job.vehicle_model or 'N/A'} - "
        f"{job.vehicle_make or 'N/A'} - {job.vehicle_registration or 'N/A'}"
    )

    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            title="Job Accepted",
            message=message
        )
        db.session.add(notif)

    db.session.commit()

    flash("You have accepted this job.", "success")
    return redirect(url_for('main.job_control', job_id=job.id))


# Decline a job
@main.route('/decline_job/<int:job_id>', methods=['POST'])
@login_required
def decline_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Only the assigned technician or admin can decline
    if current_user.role == ('technician' and
                             job.technician.user_id != current_user.id):
        flash("Unauthorized action.", "error")
        return redirect(url_for('main.staff_dashboard'))

    # Update job status
    job.accepted = False
    job.status = "Declined"

    # Create admin notifications
    technician_name = (job.technician.name if
                       job.technician else "Unknown Technician")
    message = (
        f"{technician_name} has declined the job of "
        f"{job.vehicle_color or 'N/A'} - {job.vehicle_model or 'N/A'} - "
        f"{job.vehicle_make or 'N/A'} - {job.vehicle_registration or 'N/A'}"
    )

    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            title="Job Declined",
            message=message
        )
        db.session.add(notif)

    db.session.commit()

    flash("You have declined this job.", "warning")
    return redirect(url_for('main.job_control', job_id=job.id))


# ------------------- Start Job -------------------
@main.route('/start_job/<int:job_id>', methods=['POST'])
@login_required
def start_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role == ('technician' and
                             job.technician.user_id != current_user.id):
        flash("Unauthorized action.", "error")
        return redirect(url_for('main.staff_dashboard'))

    if not job.start_time:
        job.start_time = datetime.now()
    job.status = "Running"
    db.session.commit()
    flash("Job started.", "success")
    return redirect(url_for('main.job_control', job_id=job.id))


# ------------------- Pause Job -------------------
@main.route('/pause_job/<int:job_id>', methods=['POST'])
@login_required
def pause_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role == ('technician' and
                             job.technician.user_id != current_user.id):
        return {"error": "Unauthorized action."}, 403

    now = datetime.now()

    # Add elapsed time since last start to total_work_duration
    if job.start_time:
        delta = (now - job.start_time).total_seconds()
        job.total_work_duration += int(delta)

    pause_reason = request.json.get("reason", "No reason provided")

    # Create a new pause log
    pause = PauseLog(job_id=job.id, pause_start=now, reason=pause_reason)
    db.session.add(pause)

    job.start_time = None
    job.status = "Paused"
    db.session.commit()

    return {
        "status": job.status,
        "total_elapsed": job.total_work_duration,
        "pause_id": pause.id
    }


# ------------------- Resume Job -------------------
@main.route('/resume_job/<int:job_id>', methods=['POST'])
@login_required
def resume_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role == ('technician' and
                             job.technician.user_id != current_user.id):
        return {"error": "Unauthorized action."}, 403

    now = datetime.now()

    # Close the last open pause log and calculate duration
    last_pause = (PauseLog.query.filter_by(job_id=job.id, pause_end=None)
                  .order_by(PauseLog.pause_start.desc()).first())
    if last_pause:
        last_pause.pause_end = now
        last_pause.duration = int((last_pause.pause_end -
                                  last_pause.pause_start).total_seconds())
        db.session.commit()

    job.start_time = now
    job.status = "In Progress"
    db.session.commit()

    return {
        "status": job.status,
        "total_elapsed": job.total_work_duration
    }


# ------------------- Stop Job -------------------
@main.route('/stop_job/<int:job_id>', methods=['POST'])
@login_required
def stop_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role == ('technician' and
                             job.technician.user_id != current_user.id):
        return {"error": "Unauthorized action."}, 403

    now = datetime.now()

    # Add remaining elapsed time if job was running
    if job.start_time:
        delta = (now - job.start_time).total_seconds()
        job.total_work_duration += int(delta)
        job.start_time = None

    # Close any open pause log and calculate duration
    last_pause = (PauseLog.query.filter_by(job_id=job.id, pause_end=None)
                  .order_by(PauseLog.pause_start.desc()).first())
    if last_pause:
        last_pause.pause_end = now
        last_pause.duration = int((last_pause.pause_end -
                                  last_pause.pause_start).total_seconds())
        db.session.commit()

    job.status = "Waiting for Approval"
    db.session.commit()

    return {
        "status": job.status,
        "total_elapsed": job.total_work_duration,
        "redirect_url": url_for('main.staff_jobs', tech_id=job.technician.id)
    }

# ------------------- JOB APPROVAL WORKFLOW -------------------


# Jobs waiting for admin approval
@main.route('/jobs/waiting_approval')
@login_required
def jobs_waiting_approval():
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))
    elif current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.staff_dashboard'))

    waiting_jobs = Job.query.filter_by(status="Waiting for Approval").all()
    return render_template('waiting_approval.html', jobs=waiting_jobs)


# Approve a job
@main.route('/jobs/approve/<int:job_id>', methods=['POST'])
@login_required
def approve_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.staff_dashboard'))

    job = Job.query.get_or_404(job_id)

    if job.status == 'Waiting for Approval':
        # Mark the job as completed
        job.status = 'Completed'

        pause_summary = "\n".join([
            f"{p.pause_start} - {p.pause_end or 'Still Paused'}"
            for p in job.pause_logs
        ])
        job.notes = (job.notes or '') + f"\nPause Summary:\n{pause_summary}"

        db.session.commit()
        flash('Job approved and marked as completed.', 'success')

    return redirect(url_for('main.jobs_waiting_approval'))


# Retry a job (send back to technician)
@main.route('/jobs/retry/<int:job_id>', methods=['POST'])
@login_required
def retry_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.staff_dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.status == 'Waiting for Approval':
        job.status = 'Declined at Approval'
        db.session.commit()
        flash('Job returned to technician for review.', 'warning')

    return redirect(url_for('main.jobs_waiting_approval'))


# Job completion confirmation page
@main.route('/job_complete/<int:job_id>')
@login_required
def job_complete(job_id):
    """Confirmation page for a completed job."""
    job = Job.query.get_or_404(job_id)
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "danger")
        return redirect(url_for('main.shift_dashboard'))
    return render_template('job_complete.html', job=job)


# ------------------- STAFF JOBS -------------------

@main.route('/staff_jobs/<int:tech_id>')
@login_required
def staff_jobs(tech_id):
    if current_user.role == 'reception':
        flash("Access denied. Reception users can only access dashboard.",
              "error")
        return redirect(url_for('main.shift_dashboard'))

    technician = Technician.query.get_or_404(tech_id)

    # Restrict technicians so they can only view their own jobs
    if (
        current_user.role == 'technician'
        and technician.user_id != current_user.id
    ):
        flash("Access denied. You can only view your own jobs.", "error")
        return redirect(url_for('main.staff_dashboard'))

    jobs = Job.query.filter_by(technician_id=technician.id).all()
    return render_template('staff_jobs.html', technician=technician, jobs=jobs)


# ------------------- SHIFT LOGGING -------------------

# Log shift start and end times
@main.route('/log_shift/<int:tech_id>', methods=['GET', 'POST'])
@login_required
def log_shift(tech_id):
    if current_user.role != "reception":
        flash("Access denied. Only reception can log shifts.", "error")
        return redirect(url_for('main.staff_dashboard'))

    technician = Technician.query.get_or_404(tech_id)
    today = date.today()

    # Get today's shift
    shift = Shift.query.filter(
        Shift.technician_id == tech_id,
        db.func.date(Shift.start_time) == today
    ).first()

    if request.method == 'POST':
        # Start shift
        if not shift:
            shift = Shift(
                technician_id=tech_id,
                start_time=datetime.now()
            )
            db.session.add(shift)
            db.session.commit()
            flash("Arrival time logged successfully.", "success")

        # End shift
        elif not shift.end_time:
            shift.end_time = datetime.now()
            db.session.commit()
            flash("Departure time logged successfully.", "success")

        return redirect(url_for('main.shift_dashboard'))

    return render_template('log_shift.html',
                           technician=technician, shift=shift)


# ------------------- WEEKLY SUMMARY PDF -------------------

@main.route('/weekly_summary')
@login_required
def weekly_summary_dashboard():
    if current_user.role != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('main.staff_dashboard'))

    # fetch all technicians
    techs = Technician.query.all()  # <-- variable name matches template

    return render_template('weekly_summary_dashboard.html', techs=techs)


# Generate weekly summary PDF for a technician
@main.route('/generate_weekly_summary/<int:tech_id>', methods=['POST'])
@login_required
def generate_weekly_summary(tech_id):
    if current_user.role != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('main.staff_dashboard'))

    technician = Technician.query.get_or_404(tech_id)
    week_start = date.today()
    week_end = week_start + timedelta(days=6)

    # Get shifts for the week
    shifts = Shift.query.filter(
        Shift.technician_id == tech_id,
        db.func.date(Shift.start_time) >= week_start,
        db.func.date(Shift.start_time) <= week_end
    ).all()

    # Get jobs completed in the week
    jobs = Job.query.filter(
        Job.technician_id == tech_id,
        Job.start_time >= datetime.combine(week_start, datetime.min.time()),
        Job.start_time <= datetime.combine(week_end, datetime.max.time())
    ).all()

    filename = generate_weekly_summary_pdf(technician, week_start,
                                           week_end, shifts, jobs)

    if not filename:
        flash("Could not generate weekly summary PDF.", "error")
    else:
        flash(f"Weekly summary PDF generated for {technician.name}.",
              "success")

    return redirect(url_for('main.weekly_summary_dashboard'))


# Download a specific PDF
@main.route('/download_pdf/<filename>')
@login_required
def download_pdf(filename):
    file_path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(file_path):
        flash("Requested PDF not found.", "warning")
        abort(404)
    return send_from_directory(PDF_DIR, filename, as_attachment=True)


# ------------------- PUSH NOTIFICATIONS -------------------
# Serve the service worker JavaScript
@main.route('/service-worker.js')
def service_worker():
    response = current_app.send_static_file('service-worker.js')
    response.headers['Content-Type'] = 'application/javascript'
    return response


# Provide VAPID public key to clients
@main.route('/vapid_public_key')
def get_vapid_public_key():
    return jsonify({"key": current_app.config.get("VAPID_PUBLIC_KEY", "")})


# Save a push subscription for the logged-in technician
@main.route('/save-subscription', methods=['POST'])
@login_required
def save_subscription():
    tech = Technician.query.filter_by(user_id=current_user.id).first()
    if not tech:
        return {"error": "Technician record not found for current user"}, 400

    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh')
    auth_key = keys.get('auth')

    if not endpoint or not p256dh or not auth_key:
        return {"error": "Invalid subscription payload"}, 400

    existing = PushSubscription.query.filter_by(technician_id=tech.id,
                                                endpoint=endpoint).first()

    if existing:
        updated = False
        if existing.p256dh != p256dh:
            existing.p256dh = p256dh
            updated = True
        if existing.auth != auth_key:
            existing.auth = auth_key
            updated = True
        if updated:
            db.session.commit()
    else:
        sub = PushSubscription(technician_id=tech.id, endpoint=endpoint,
                               p256dh=p256dh, auth=auth_key)
        db.session.add(sub)
        db.session.commit()

    return {"status": "Subscription saved"}


# Remove a push subscription for the logged-in technician
@main.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """
    Remove a push subscription for the logged-in technician.
    """
    data = request.get_json()
    endpoint = data.get("endpoint")

    tech = Technician.query.filter_by(user_id=current_user.id).first()
    if not tech:
        return {"status": "Technician not found"}, 404

    sub = PushSubscription.query.filter_by(technician_id=tech.id,
                                           endpoint=endpoint).first()

    if sub:
        db.session.delete(sub)
        db.session.commit()
        return {"status": "Unsubscribed"}, 200

    return {"status": "Not found"}, 404


# Send a test notification to the logged-in technician i will remove this
# route in published version
@main.route('/test_notification')
@login_required
def test_notification():
    tech = Technician.query.filter_by(user_id=current_user.id).first()
    if not tech:
        flash("Only technicians can test notifications.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    from app.utils.notifications import send_push_to_technician
    send_push_to_technician(
        tech.id,
        "Test Notification",
        "Test notification from Workshop Manager",
        url="/staff"
    )
    flash("Test notification sent. Check your device.", "success")
    return redirect(url_for("main.staff_dashboard"))


# ------------------- ADMIN LIVE JOBS -------------------

# Admin view of live jobs
@main.route('/live_jobs')
@login_required
def live_jobs():
    """Admin view of live jobs."""
    if current_user.role != 'admin':
        flash("Access denied. Only admins can view live jobs.", "danger")
        return redirect(url_for('main.shift_dashboard'))

    jobs = Job.query.filter(Job.status.notin_(["Completed", "Declined"])).all()
    return render_template('live_jobs.html', jobs=jobs)


# For live AJAX updates
@main.route('/live_jobs_data')
@login_required
def live_jobs_data():
    if current_user.role != 'admin':
        return "Access denied", 403

    jobs = Job.query.filter(Job.status.notin_(["Completed", "Declined"])).all()
    return render_template('_live_jobs_table.html', jobs=jobs)


# Admin actions on jobs
@main.route('/admin_action/<int:job_id>/<string:action>', methods=['POST'])
@login_required
def admin_action(job_id, action):
    """Allow admin to take direct actions on jobs."""
    if current_user.role != 'admin':
        flash("Access denied. Only admins can manage jobs.", "danger")
        return redirect(url_for('main.shift_dashboard'))

    job = Job.query.get_or_404(job_id)

    if action == "stop":
        job.status = "Waiting for Approval"
        job.end_time = datetime.now()

    elif action == "pause":
        pause = PauseLog(job_id=job.id,
                         paused_at=datetime.now(),
                         reason="Paused by Admin")
        db.session.add(pause)
        job.status = "Paused"

    elif action == "resume":
        pause = (PauseLog.query
                 .filter_by(job_id=job.id, resumed_at=None)
                 .order_by(PauseLog.paused_at.desc())
                 .first())
        if pause:
            pause.resumed_at = datetime.now()
        job.status = "In Progress"

    db.session.commit()
    flash(f"Admin action '{action}' performed on job {job.id}.", "info")
    return redirect(url_for('main.live_jobs'))

