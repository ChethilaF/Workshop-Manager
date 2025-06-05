from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username='tech1').first():
        tech = User(
            username='tech1',
            role='technician',
            active=True
        )
        tech.set_password('tech123')
        db.session.add(tech)
        db.session.commit()
        print("✅ Technician user created.")
    else:
        print("Technician user already exists.")
