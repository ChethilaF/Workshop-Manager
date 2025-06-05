from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app.models import User, Customer, Technician, Job, PauseLog
from app.utils.pdf_generator import generate_job_pdf

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', role='user')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password_hash=generate_password_hash(request.form['password']),
            role=request.form['role']
        )
        db.session.add(user)
        db.session.commit()

        if user.role == 'technician':
            tech = Technician(
                name=request.form['name'],
                email=request.form['email'],
                phone=request.form['phone'],
                user_id=user.id
            )
            db.session.add(tech)

        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@main.route('/technician_dashboard')
@login_required
def technician_dashboard():
    if current_user.role != 'technician':
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    tech = Technician.query.filter_by(user_id=current_user.id).first()
    jobs = Job.query.filter_by(technician_id=tech.id).all()
    return render_template('technician_dashboard.html', jobs=jobs)

@main.route('/customer_dashboard', methods=['GET', 'POST'])
@login_required
def customer_dashboard():
    if request.method == 'POST':
        reg = request.form['rego']
        job = Job.query.filter_by(vehicle_registration=reg).first()
        return render_template('customer_dashboard.html', status=job)
    return render_template('customer_dashboard.html')

# Customers
@main.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@main.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        customer = Customer(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            address=request.form['address']
        )
        db.session.add(customer)
        db.session.commit()
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

# Technicians
@main.route('/technicians')
@login_required
def technicians():
    techs = Technician.query.all()
    return render_template('technicians.html', technicians=techs)

@main.route('/add_technician', methods=['GET', 'POST'])
@login_required
def add_technician():
    if request.method == 'POST':
        tech = Technician(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            specialization=request.form['specialization']
        )
        db.session.add(tech)
        db.session.commit()
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

# Jobs
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
        job = Job(
            description=request.form['description'],
            start_date=request.form['start_date'],
            end_date=request.form['end_date'],
            status=request.form['status'],
            total_cost=request.form['total_cost'],
            customer_id=request.form['customer_id'],
            technician_id=request.form['technician_id'],
            vehicle_registration=request.form['vehicle_registration']
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('main.jobs'))
    return render_template('add_job.html', customers=customers, technicians=technicians)

@main.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    customers = Customer.query.all()
    technicians = Technician.query.all()
    if request.method == 'POST':
        job.description = request.form['description']
        job.start_date = request.form['start_date']
        job.end_date = request.form['end_date']
        job.status = request.form['status']
        job.total_cost = request.form['total_cost']
        job.customer_id = request.form['customer_id']
        job.technician_id = request.form['technician_id']
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

        if action == 'start':
            job.start_time = datetime.utcnow()

        elif action == 'pause':
            pause = PauseLog(
                job_id=job.id,
                paused_at=datetime.utcnow(),
                reason=request.form.get('pause_reason', '')
            )
            db.session.add(pause)

        elif action == 'resume':
            pause = PauseLog.query.filter_by(job_id=job.id, resumed_at=None).order_by(PauseLog.paused_at.desc()).first()
            if pause:
                pause.resumed_at = datetime.utcnow()
                job.total_work_duration += int((pause.resumed_at - pause.paused_at).total_seconds())

        elif action == 'stop':
            pause = PauseLog.query.filter_by(job_id=job.id, resumed_at=None).order_by(PauseLog.paused_at.desc()).first()
            if pause:
                pause.resumed_at = datetime.utcnow()
                job.total_work_duration += int((pause.resumed_at - pause.paused_at).total_seconds())
            job.end_time = datetime.utcnow()
            generate_job_pdf(job, job.technician)
            return redirect(url_for('main.job_complete', job_id=job.id))

        db.session.commit()
    return render_template('job_control.html', job=job)

@main.route('/job_complete/<int:job_id>')
@login_required
def job_complete(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_complete.html', job=job)

@main.route('/download_job_pdf/<int:job_id>')
@login_required
def download_job_pdf(job_id):
    filename = f"job_{job_id}_summary.pdf"
    return send_from_directory('app/static/pdfs', filename, as_attachment=True)

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
    return redirect(url_for('main.technician_dashboard'))
