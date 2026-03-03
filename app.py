"""
==============================================================================
Online Voting System - Main Application
==============================================================================
This is the main Flask application file for the Online Voting System.
It includes:
- Database models and initialization
- Authentication routes (login, register, logout)
- Admin routes (dashboard, add candidates, view voters, results)
- Voter routes (dashboard, view candidates, cast vote)
- JWT authentication
- Role-based access control
- Vote encryption
- Email verification

Author: Online Voting System Team
==============================================================================
"""

import os
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from config import get_config

# =============================================================================
# Application Factory
# =============================================================================

def create_app(config_name='development'):
    """
    Application factory function to create and configure the Flask app.
    
    Args:
        config_name: The name of the configuration to use
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config())
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt_manager.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.voter import voter_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(voter_bp, url_prefix='/voter')
    
    # Initialize database
    with app.app_context():
        db.create_all()
        create_default_admin()
    
    # =============================================================================
    # Error Handlers
    # =============================================================================
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('500.html', error=error), 500
    
    @app.route('/')
    def index():
        """Home page route."""
        return render_template('index.html')
    
    return app


# =============================================================================
# Initialize Extensions
# =============================================================================

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt_manager = JWTManager()
mail = Mail()
login_manager = LoginManager()

# =============================================================================
# Login Manager User Loader
# =============================================================================

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


# =============================================================================
# Database Models
# =============================================================================

class User(UserMixin, db.Model):
    """
    User model representing voters and administrators.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        password_hash: Hashed password
        role: User role (admin or voter)
        is_verified: Email verification status
        verification_token: Token for email verification
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='voter')
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('Vote', backref='voter', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify the user's password."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    def has_voted(self):
        """Check if user has already voted."""
        return Vote.query.filter_by(voter_id=self.id).first() is not None
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Candidate(db.Model):
    """
    Candidate model representing election candidates.
    
    Attributes:
        id: Primary key
        name: Candidate's full name
        party: Political party
        description: Candidate description
        image_url: Candidate photo URL
        is_active: Active status in election
        created_at: Creation timestamp
    """
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(150))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('Vote', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Candidate {self.name}>'
    
    def to_dict(self):
        """Convert candidate to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'party': self.party,
            'description': self.description,
            'image_url': self.image_url,
            'is_active': self.is_active
        }


class Vote(db.Model):
    """
    Vote model representing a cast vote with encryption.
    
    Attributes:
        id: Primary key
        voter_id: Foreign key to User
        candidate_id: Foreign key to Candidate
        encrypted_vote: Encrypted vote data
        vote_hash: Hash for vote verification
        voted_at: Timestamp of vote
    """
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    encrypted_vote = db.Column(db.Text, nullable=False)
    vote_hash = db.Column(db.String(255), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Vote by User {self.voter_id} for Candidate {self.candidate_id}>'
    
    def to_dict(self):
        """Convert vote to dictionary."""
        return {
            'id': self.id,
            'voter_id': self.voter_id,
            'candidate_id': self.candidate_id,
            'vote_hash': self.vote_hash,
            'voted_at': self.voted_at.isoformat() if self.voted_at else None
        }


class ElectionSettings(db.Model):
    """
    Election settings model for configuration.
    
    Attributes:
        id: Primary key
        election_name: Name of the election
        election_description: Description
        start_date: Election start time
        end_date: Election end time
        is_active: Election status
    """
    __tablename__ = 'election_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.String(100), default='General Election')
    election_description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ElectionSettings {self.election_name}>'


# =============================================================================
# Utility Functions
# =============================================================================

def create_default_admin():
    """Create a default admin user if none exists."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_verified=True,
            verification_token=secrets.token_urlsafe(32)
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        
        # Create default election settings
        settings = ElectionSettings.query.first()
        if not settings:
            settings = ElectionSettings(
                election_name='General Election 2024',
                election_description='Annual General Election',
                is_active=True
            )
            db.session.add(settings)
        
        db.session.commit()
        print("Default admin user created: admin / Admin@123")


def encrypt_vote(vote_data, key):
    """
    Encrypt vote data using Fernet symmetric encryption.
    
    Args:
        vote_data: The vote data to encrypt
        key: Encryption key
        
    Returns:
        Encrypted vote data as string
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Generate a valid Fernet key from the provided key
    key_bytes = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    f = Fernet(fernet_key)
    
    encrypted = f.encrypt(vote_data.encode())
    return encrypted.decode()


def decrypt_vote(encrypted_data, key):
    """
    Decrypt vote data.
    
    Args:
        encrypted_data: The encrypted vote data
        key: Encryption key
        
    Returns:
        Decrypted vote data
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    key_bytes = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    f = Fernet(fernet_key)
    
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()


def generate_vote_hash(voter_id, candidate_id, encryption_key):
    """Generate a hash for vote verification."""
    import hashlib
    data = f"{voter_id}-{candidate_id}-{encryption_key}-{datetime.utcnow()}"
    return hashlib.sha256(data.encode()).hexdigest()


def send_verification_email(user):
    """Send email verification link to user."""
    from flask import current_app
    
    token = user.verification_token
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg = Message(
        'Verify Your Email - Online Voting System',
        recipients=[user.email]
    )
    msg.body = f'''
    Welcome to Online Voting System!
    
    Please verify your email by clicking the link below:
    {verify_url}
    
    If you did not create this account, please ignore this email.
    
    Best regards,
    Online Voting System Team
    '''
    msg.html = f'''
    <html>
    <body>
        <h2>Welcome to Online Voting System!</h2>
        <p>Please verify your email by clicking the button below:</p>
        <a href="{verify_url}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Verify Email</a>
        <p>Or copy this link: {verify_url}</p>
        <p>If you did not create this account, please ignore this email.</p>
    </body>
    </html>
    '''
    
    mail.send(msg)


# =============================================================================
# WTForms Classes
# =============================================================================

class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email already exists."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class LoginForm(FlaskForm):
    """Form for user login."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class CandidateForm(FlaskForm):
    """Form for adding/editing candidates."""
    name = StringField('Candidate Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    party = StringField('Political Party', validators=[
        Length(max=150, message='Party name must be less than 150 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=1000, message='Description must be less than 1000 characters')
    ])
    image_url = StringField('Image URL', validators=[Optional()])
    submit = SubmitField('Add Candidate')


class VoteForm(FlaskForm):
    """Form for casting a vote."""
    candidate = SelectField('Select Candidate', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Cast Vote')


# =============================================================================
# Decorators for Role-Based Access Control
# =============================================================================

def admin_required(f):
    """
    Decorator to require admin role for a route.
    Usage: @admin_required
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def voter_required(f):
    """
    Decorator to require voter role for a route.
    Usage: @voter_required
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.is_admin():
            flash('Admin users cannot vote.', 'warning')
            return redirect(url_for('admin.dashboard'))
        if not current_user.is_verified:
            flash('Please verify your email before voting.', 'warning')
            return redirect(url_for('auth.unverified'))
        return f(*args, **kwargs)
    return decorated_function


def verified_required(f):
    """
    Decorator to require verified email for a route.
    Usage: @verified_required
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_verified:
            flash('Please verify your email to access this feature.', 'warning')
            return redirect(url_for('auth.unverified'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
