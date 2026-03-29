from support.app import app
from support.models import db, User

with app.app_context():
    db.create_all()

    # Create default admin
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", role="admin")
        db.session.add(admin)

    if not User.query.filter_by(username="user").first():
        user = User(username="user", password="user123", role="user")
        db.session.add(user)

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)