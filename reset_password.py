from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='john').first()
    if user:
        user.set_password('john123')  # Set correct hashed password
        db.session.commit()
        print("✅ Password reset for john")
    else:
        print("❌ User not found")
