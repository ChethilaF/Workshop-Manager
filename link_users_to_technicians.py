from app import create_app, db
from app.models import User, Technician

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='john').first()
    tech = Technician.query.filter_by(name='John Smith').first()
    if user and tech:
        tech.user_id = user.id
        db.session.commit()
