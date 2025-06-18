from flask_login import UserMixin
from vaultview.db import db
from datetime import datetime
from vaultview.utils import get_ist_now

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ScanResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    result_type = db.Column(db.String(50), nullable=False)  # 'SSL' or 'DNS'
    result_data = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=get_ist_now, nullable=False) 