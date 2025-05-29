from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Customer
from flask import session
from app.models import User
from app import db, login_manager
from datetime import datetime
from app.models import Technician
from app.models import Job 
from app.models import PauseLog
from flask import send_file
from flask import request
from app.utils.pdf_generator import generate_job_pdf

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))  # redirect logged-in users

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('home.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@main.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded shared login (you can replace with a secure check later)
        if username == 'customer' and password == 'vehicle123':
            session['customer_logged_in'] = True
            return redirect(url_for('main.customer_home'))
        else:
            flash('Invalid credentials for customer access.', 'danger')

    return render_template('customer_login.html')


@main.route('/customer_home', methods=['GET', 'POST'])
def customer_home():
    if not session.get('customer_logged_in'):
        return redirect(url_for('main.customer_login'))

    status = None
    if request.method == 'POST':
        reg_number = request.form['reg_number']
        job = Job.query.filter_by(vehicle_registration=reg_number).first()

        if job:
            status = {
                'description': job.description,
                'status': job.status,
                'start_date': job.start_date,
                'end_date': job.end_date,
                'technician': job.technician.name
            }
        else:
            flash('No job found for that registration.', 'warning')

    return render_template('customer_home.html', status=status)


@main.route('/customers')
@login_required
def customers():
    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)


@main.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        new_customer = Customer(name=name, email=email, phone=phone, address=address)
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('main.customers'))

    return render_template('add_customer.html')


@main.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        db.session.commit()
        flash("Customer updated successfully!", "success")
        return redirect(url_for('main.customers'))
    return render_template('edit_customer.html', customer=customer)


@main.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted.", "info")
    return redirect(url_for('main.customers'))


@main.route('/technicians')
@login_required
def technicians():
    all_techs = Technician.query.all()
    return render_template('technicians.html', technicians=all_techs)


@main.route('/technicians/add', methods=['GET', 'POST'])
@login_required
def add_technician():
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        specialization = request.form['specialization']
        new_tech = Technician(name=name, email=email, phone=phone, specialization=specialization)
        db.session.add(new_tech)
        db.session.commit()
        flash('Technician added successfully!', 'success')
        return redirect(url_for('main.technicians'))

    return render_template('add_technician.html')


@main.route('/technicians/edit/<int:technician_id>', methods=['GET', 'POST'])
@login_required
def edit_technician(technician_id):
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    technician = Technician.query.get_or_404(technician_id)
    if request.method == 'POST':
        technician.name = request.form['name']
        technician.email = request.form['email']
        technician.phone = request.form['phone']
        technician.specialization = request.form['specialization']
        db.session.commit()
        flash("Technician updated successfully!", "success")
        return redirect(url_for('main.technicians'))
    return render_template('edit_technician.html', technician=technician)


@main.route('/technicians/delete/<int:technician_id>', methods=['POST'])
@login_required
def delete_technician(technician_id):
    technician = Technician.query.get_or_404(technician_id)
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    if technician.jobs:
        flash("Cannot delete technician assigned to a job.", "danger")
        return redirect(url_for('main.technicians'))

    db.session.delete(technician)
    db.session.commit()
    flash("Technician deleted.", "info")
    return redirect(url_for('main.technicians'))


@main.route('/technician_dashboard')
@login_required
def technician_dashboard():
    technicians = Technician.query.all()
    user_tech = Technician.query.filter_by(user_id=current_user.id).first() if current_user.role == 'technician' else None
    return render_template('technician_dashboard.html', technicians=technicians, user_tech=user_tech)


@main.route('/technician_jobs/<int:tech_id>', methods=['POST'])
@login_required
def view_technician_jobs(tech_id):
    tech = Technician.query.get_or_404(tech_id)
    if current_user.role != 'admin' and tech.user_id != current_user.id:
        return "Unauthorized", 403

    jobs = tech.jobs
    return render_template('technician_jobs.html', technician=tech, jobs=jobs)


@main.route('/jobs')
@login_required
def jobs():
    all_jobs = Job.query.all()
    return render_template('jobs.html', jobs=all_jobs)


@main.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    customers = Customer.query.all()
    technicians = Technician.query.all()

    if request.method == 'POST':
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        total_cost = request.form['total_cost']
        customer_id = request.form['customer_id']
        technician_id = request.form['technician_id']
        vehicle_registration = request.form['vehicle_registration']

        # Convert dates safely
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

        job = Job(
            description=description,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status=status,
            total_cost=total_cost or 0,
            customer_id=customer_id,
            technician_id=technician_id,
            vehicle_registration=vehicle_registration
        )

        db.session.add(job)
        db.session.commit()
        flash('Job created successfully.')
        return redirect(url_for('main.jobs'))

    return render_template('add_job.html', customers=customers, technicians=technicians)


@main.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        job.description = request.form['description']
        job.status = request.form['status']
        job.total_cost = request.form['total_cost']
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        job.start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        job.end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        job.customer_id = request.form['customer_id']
        job.technician_id = request.form['technician_id']
        job.vehicle_registration = request.form['vehicle_registration']
        
        db.session.commit()
        flash('✅ Job updated successfully.', 'success')
        return redirect(url_for('main.jobs'))

    customers = Customer.query.all()
    technicians = Technician.query.all()
    return render_template('edit_job.html', job=job, customers=customers, technicians=technicians)


@main.route('/jobs/delete/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('main.dashboard'))
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "info")
    return redirect(url_for('main.jobs'))


@main.route('/job_control/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_control(job_id):
    job = Job.query.get_or_404(job_id)

    if current_user.role != 'admin' and job.technician.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'start':
            job.start_time = datetime.utcnow()
            db.session.commit()
        
        elif action == 'pause':
            reason = request.form.get('pause_reason', '')
            pause = PauseLog(
                job_id=job.id,
                paused_at=datetime.utcnow(),
                reason=reason
            )
            db.session.add(pause)
            db.session.commit()
        
        elif action == 'resume':
            last_pause = PauseLog.query.filter_by(job_id=job.id, resumed_at=None).order_by(PauseLog.paused_at.desc()).first()
            if last_pause:
                last_pause.resumed_at = datetime.utcnow()
                paused_duration = (last_pause.resumed_at - last_pause.paused_at).total_seconds()
                job.total_work_duration += int(paused_duration)
                db.session.commit()

        elif action == 'stop':
            last_pause = PauseLog.query.filter_by(job_id=job.id, resumed_at=None).order_by(PauseLog.paused_at.desc()).first()
            if last_pause:
                last_pause.resumed_at = datetime.utcnow()
                paused_duration = (last_pause.resumed_at - last_pause.paused_at).total_seconds()
                job.total_work_duration += int(paused_duration)

            job.end_time = datetime.utcnow()
            db.session.commit()

            technician = job.technician
            generate_job_pdf(job, technician)

            flash("Job completed and PDF summary generated.")
            return redirect(url_for('main.job_complete', job_id=job.id))
                   
    return render_template('job_control.html', job=job)


@main.route('/accept_job/<int:job_id>', methods=['POST'])
@login_required
def accept_job(job_id):
    job = Job.query.get_or_404(job_id)

    if current_user.role != 'admin':
        technician = Technician.query.filter_by(user_id=current_user.id).first()
        if not technician or job.technician_id != technician.id:
            flash("Access denied.")
            return redirect(url_for('main.technician_jobs'))
        
    if current_user.role != 'technician':
        flash("Only technicians can accept jobs.")
        return redirect(url_for('main.dashboard'))

    technician = Technician.query.filter_by(user_id=current_user.id).first()
    if job.technician_id != technician.id:
        flash("You can only accept your own assigned jobs.")
        return redirect(url_for('main.technician_jobs'))

    job.accepted = True
    db.session.commit()
    flash("Job accepted!")
    return redirect(url_for('main.job_control', job_id=job.id))


@main.route('/job_pdf/<int:job_id>')
@login_required
def download_job_pdf(job_id):
    job = Job.query.get_or_404(job_id)
    technician = job.technician

    pdf_path = generate_job_pdf(job, technician)
    return send_file(pdf_path, as_attachment=True)


@main.route('/job_complete/<int:job_id>')
@login_required
def job_complete(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_complete.html', job=job)


@main.route('/staff')
@login_required
def staff_overview():
    from app.models import Technician
    techs = Technician.query.all()
    return render_template('staff_dashboard.html', techs=techs)


@main.route('/staff/<int:tech_id>')
@login_required
def staff_jobs(tech_id):

    if current_user.role != 'admin':
        if current_user.role == 'technician' and current_user.id != tech_id:
            flash("Access denied: you can only view your own jobs.", "danger")
            return redirect(url_for('main.dashboard'))

    tech = Technician.query.get_or_404(tech_id)
    jobs = tech.jobs
    return render_template('staff_jobs.html', technician=tech, jobs=jobs)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('main.register'))

        new_user = User(username=username, role=role, active=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if role == 'technician':
            tech = Technician(name=name, email=email, phone=phone, specialization='', user_id=new_user.id)
            db.session.add(tech)

        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')
