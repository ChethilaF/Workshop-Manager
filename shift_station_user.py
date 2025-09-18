from app import create_app, db
from app.models import User

# Create the Flask app
app = create_app()

# Use application context
with app.app_context():
    # Create the reception / shift station user
    shift_station = User(username="r", role="reception", active=True)
    shift_station.set_password("qwerty")

    # Add to DB
    db.session.add(shift_station)
    db.session.commit()
    print("Shift station user created successfully!")
