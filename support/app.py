from flask import Flask
from flask_cors import CORS
from support.models import db

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "safeshire_secret_key"

CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

from support import routes