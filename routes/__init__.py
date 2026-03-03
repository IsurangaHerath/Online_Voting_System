# =============================================================================
# Routes Package Initialization
# =============================================================================
# This file initializes the routes package for the Online Voting System.
# It imports all route blueprints for registration with the Flask app.
# =============================================================================

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.voter import voter_bp

__all__ = ['auth_bp', 'admin_bp', 'voter_bp']
