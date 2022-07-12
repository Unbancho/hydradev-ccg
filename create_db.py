from app import app
from models import db

"""
Utility script to create the database.
"""

db.init_app(app)
with app.app_context():
    db.create_all()
