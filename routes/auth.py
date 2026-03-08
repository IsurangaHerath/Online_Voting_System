import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db, User, Vote, send_verification_email, encrypt_vote
from app import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voter.dashboard'))
    
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='voter',
                is_verified=False,
                verification_token=secrets.token_urlsafe(32)
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            try:
                send_verification_email(user)
                flash('Registration successful! Please check your email to verify your account.', 'success')
            except Exception as e:
                current_app.logger.error(f'Failed to send verification email: {e}')
                flash('Registration successful! However, we could not send the verification email. Please contact support.', 'warning')
            
            return redirect(url_for('auth.register_success'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html', form=form)


@auth_bp.route('/register-success')
def register_success():
    """Display registration success page."""
    return render_template('register_success.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voter.dashboard'))
    
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voter.dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Email verification."""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
    
    try:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Email verified successfully! You can now login.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Verification error: {e}')
        flash('An error occurred during verification. Please try again.', 'danger')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/unverified')
@login_required
def unverified():
    """Display page for unverified users."""
    if current_user.is_verified:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voter.dashboard'))
    
    return render_template('verify_email.html')


@auth_bp.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    """Resend verification email."""
    if current_user.is_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('index'))
    
    try:
        send_verification_email(current_user)
        flash('Verification email sent! Please check your inbox.', 'success')
    except Exception as e:
        current_app.logger.error(f'Failed to resend verification email: {e}')
        flash('Failed to send verification email. Please try again later.', 'danger')
    
    return redirect(url_for('auth.unverified'))


# API Routes (JWT Authentication)
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API login for JWT token generation."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_verified:
        return jsonify({'error': 'Email not verified'}), 401
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims={'role': user.role, 'username': user.username}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API registration."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    try:
        user = User(
            username=username,
            email=email,
            role='voter',
            is_verified=False,
            verification_token=secrets.token_urlsafe(32)
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/api/me', methods=['GET'])
@jwt_required()
def api_me():
    """Get current user information from JWT token."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/api/protected', methods=['GET'])
@jwt_required()
def api_protected():
    """Example protected API route."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    return jsonify({
        'message': 'Access granted to protected route',
        'user': user.username,
        'role': user.role
    }), 200
