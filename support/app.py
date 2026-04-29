from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
from support.models import db, User  

app = Flask(name) 

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workers.db" app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False app.secret_key = "safehire-secret-key" 

db.init_app(app) 

login_manager = LoginManager() login_manager.init_app(app) login_manager.login_view = "login" 

@login_manager.user_loader def load_user(user_id): return User.query.get(int(user_id)) 

from support import routes 

with app.app_context(): db.create_all() 

if name == 'main': app.run(debug=True) 