from flask import Flask
from support.models import db

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "safehire-secret-key"

db.init_app(app)

with app.app_context():
    db.create_all()

from support import routes