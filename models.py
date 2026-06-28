from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(255), nullable=True)
    verified = db.Column(db.Boolean, default=False)

def save_token_for_user(email, token):
    user = User.query.filter_by(email=email).first()
    if user:
        user.token = token
        db.session.commit()
