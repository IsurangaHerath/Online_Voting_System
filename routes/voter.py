"""
==============================================================================
Voter Routes
==============================================================================
This file contains all voter-related routes for the Online Voting System.
Only verified voters can access these routes.

Routes:
    /voter/dashboard - Voter dashboard
    /voter/candidates - View all candidates
    /voter/vote/<candidate_id> - Cast vote for a candidate
    /voter/confirmation - Vote confirmation page
    /voter/status - Check voting status
==============================================================================
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required as flask_jwt_required, get_jwt_identity
from app import db, User, Candidate, Vote, ElectionSettings
from app import encrypt_vote, generate_vote_hash
from app import voter_required, verified_required
from datetime import datetime

# Create voter blueprint
voter_bp = Blueprint('voter', __name__)


# =============================================================================
# Routes
# =============================================================================

@voter_bp.route('/dashboard')
@login_required
@voter_required
def dashboard():
    """
    Voter dashboard route.
    
    Displays:
        - User profile information
        - Voting status
        - Election information
    """
    # Check if user has voted
    has_voted = Vote.query.filter_by(voter_id=current_user.id).first() is not None
    
    # Get vote details if voted
    vote = None
    voted_for = None
    if has_voted:
        vote = Vote.query.filter_by(voter_id=current_user.id).first()
        if vote:
            voted_for = Candidate.query.get(vote.candidate_id)
    
    # Get election settings
    election = ElectionSettings.query.first()
    
    # Get active candidates count
    candidates_count = Candidate.query.filter_by(is_active=True).count()
    
    return render_template(
        'voter/dashboard.html',
        has_voted=has_voted,
        vote=vote,
        voted_for=voted_for,
        election=election,
        candidates_count=candidates_count
    )


@voter_bp.route('/candidates')
@login_required
@voter_required
def candidates():
    """View all active candidates."""
    candidates = Candidate.query.filter_by(is_active=True).all()
    
    # Check if user has already voted
    has_voted = Vote.query.filter_by(voter_id=current_user.id).first() is not None
    
    return render_template(
        'voter/candidates.html',
        candidates=candidates,
        has_voted=has_voted
    )


@voter_bp.route('/vote/<int:candidate_id>', methods=['GET', 'POST'])
@login_required
@voter_required
@verified_required
def vote(candidate_id):
    """
    Cast vote for a candidate.
    
    Args:
        candidate_id: ID of candidate to vote for
    
    GET: Display vote confirmation
    POST: Process and save vote
    """
    # Check if election is active
    election = ElectionSettings.query.first()
    if not election or not election.is_active:
        flash('Voting is not currently active.', 'warning')
        return redirect(url_for('voter.candidates'))
    
    # Check if user has already voted
    existing_vote = Vote.query.filter_by(voter_id=current_user.id).first()
    if existing_vote:
        flash('You have already cast your vote.', 'warning')
        return redirect(url_for('voter.dashboard'))
    
    # Get candidate
    candidate = Candidate.query.get_or_404(candidate_id)
    
    if not candidate.is_active:
        flash('This candidate is not active.', 'warning')
        return redirect(url_for('voter.candidates'))
    
    if request.method == 'POST':
        try:
            # Prepare vote data
            vote_data = f"voter:{current_user.id},candidate:{candidate.id},timestamp:{datetime.utcnow().isoformat()}"
            
            # Encrypt vote data
            encryption_key = current_app.config.get('VOTE_ENCRYPTION_KEY', 'default-key')
            encrypted_vote = encrypt_vote(vote_data, encryption_key)
            
            # Generate vote hash for verification
            vote_hash = generate_vote_hash(
                current_user.id,
                candidate.id,
                encryption_key
            )
            
            # Create vote record
            vote = Vote(
                voter_id=current_user.id,
                candidate_id=candidate.id,
                encrypted_vote=encrypted_vote,
                vote_hash=vote_hash
            )
            
            db.session.add(vote)
            db.session.commit()
            
            flash('Your vote has been cast successfully!', 'success')
            return redirect(url_for('voter.confirmation'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error casting vote: {e}')
            flash('An error occurred while casting your vote. Please try again.', 'danger')
    
    return render_template(
        'voter/vote.html',
        candidate=candidate
    )


@voter_bp.route('/confirmation')
@login_required
@voter_required
def confirmation():
    """Display vote confirmation page."""
    # Get the vote details
    vote = Vote.query.filter_by(voter_id=current_user.id).first()
    
    if not vote:
        flash('No vote found.', 'warning')
        return redirect(url_for('voter.candidates'))
    
    candidate = Candidate.query.get(vote.candidate_id)
    
    return render_template(
        'voter/confirmation.html',
        vote=vote,
        candidate=candidate
    )


@voter_bp.route('/status')
@login_required
@voter_required
def status():
    """Check voting status."""
    has_voted = Vote.query.filter_by(voter_id=current_user.id).first() is not None
    
    vote = None
    candidate = None
    if has_voted:
        vote = Vote.query.filter_by(voter_id=current_user.id).first()
        if vote:
            candidate = Candidate.query.get(vote.candidate_id)
    
    return jsonify({
        'has_voted': has_voted,
        'vote': vote.to_dict() if vote else None,
        'candidate': candidate.to_dict() if candidate else None
    }), 200


# =============================================================================
# API Routes
# =============================================================================

@voter_bp.route('/api/candidates')
@login_required
@voter_required
def api_candidates():
    """API endpoint for candidate list."""
    candidates = Candidate.query.filter_by(is_active=True).all()
    
    return jsonify({
        'candidates': [c.to_dict() for c in candidates]
    }), 200


@voter_bp.route('/api/vote', methods=['POST'])
@login_required
@voter_required
@flask_jwt_required()
def api_vote():
    """
    API endpoint to cast vote.
    
    Request JSON:
        candidate_id: ID of candidate to vote for
    
    Response JSON:
        message: Success/error message
        vote: Vote details
    """
    # Check if election is active
    election = ElectionSettings.query.first()
    if not election or not election.is_active:
        return jsonify({'error': 'Voting is not currently active'}), 400
    
    # Check if user has already voted
    existing_vote = Vote.query.filter_by(voter_id=current_user.id).first()
    if existing_vote:
        return jsonify({'error': 'You have already cast your vote'}), 400
    
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    
    if not candidate_id:
        return jsonify({'error': 'Candidate ID is required'}), 400
    
    # Get candidate
    candidate = Candidate.query.get(candidate_id)
    if not candidate or not candidate.is_active:
        return jsonify({'error': 'Invalid candidate'}), 400
    
    try:
        # Prepare and encrypt vote
        vote_data = f"voter:{current_user.id},candidate:{candidate.id},timestamp:{datetime.utcnow().isoformat()}"
        encryption_key = current_app.config.get('VOTE_ENCRYPTION_KEY', 'default-key')
        encrypted_vote = encrypt_vote(vote_data, encryption_key)
        
        # Generate vote hash
        vote_hash = generate_vote_hash(current_user.id, candidate.id, encryption_key)
        
        # Create vote
        vote = Vote(
            voter_id=current_user.id,
            candidate_id=candidate.id,
            encrypted_vote=encrypted_vote,
            vote_hash=vote_hash
        )
        
        db.session.add(vote)
        db.session.commit()
        
        return jsonify({
            'message': 'Vote cast successfully',
            'vote': vote.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'API vote error: {e}')
        return jsonify({'error': 'Failed to cast vote'}), 500
