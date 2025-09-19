from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

admin = User(
    username='admin',
    email='chethilafernando77@gmail.com',
    role='admin'
)
admin.set_password('admin123')

db.session.add(admin)
db.session.commit()

print("Admin user created successfully.")
