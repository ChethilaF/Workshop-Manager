from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin', active=True)
        admin.set_password('admin123')  # ← this hashes the password
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("ℹ️ Admin user already exists.")
