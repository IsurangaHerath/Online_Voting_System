"""
==============================================================================
Admin Routes
==============================================================================
This file contains all admin-related routes for the Online Voting System.
Only users with 'admin' role can access these routes.

Routes:
    /admin/dashboard - Admin dashboard
    /admin/add-candidate - Add new candidate
    /admin/view-voters - View all registered voters
    /admin/results - View voting results
    /admin/delete-candidate/<id> - Delete candidate
    /admin/toggle-candidate/<id> - Toggle candidate status
    /admin/election-settings - Configure election settings
==============================================================================
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db, User, Candidate, Vote, ElectionSettings
from app import CandidateForm
from app import admin_required
from datetime import datetime

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)


# =============================================================================
# Routes
# =============================================================================

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard route.
    
    Displays:
        - Total voters count
        - Total candidates count
        - Total votes cast
        - Recent registrations
    """
    total_voters = User.query.filter_by(role='voter').count()
    verified_voters = User.query.filter_by(role='voter', is_verified=True).count()
    total_candidates = Candidate.query.count()
    active_candidates = Candidate.query.filter_by(is_active=True).count()
    total_votes = Vote.query.count()
    
    # Get election settings
    election = ElectionSettings.query.first()
    
    # Get recent voters
    recent_voters = User.query.filter_by(role='voter').order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_voters=total_voters,
        verified_voters=verified_voters,
        total_candidates=total_candidates,
        active_candidates=active_candidates,
        total_votes=total_votes,
        election=election,
        recent_voters=recent_voters
    )


@admin_bp.route('/add-candidate', methods=['GET', 'POST'])
@login_required
@admin_required
def add_candidate():
    """
    Add new candidate route.
    
    GET: Display candidate form
    POST: Process and save new candidate
    """
    form = CandidateForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            candidate = Candidate(
                name=form.name.data,
                party=form.party.data,
                description=form.description.data,
                image_url=form.image_url.data,
                is_active=True
            )
            
            db.session.add(candidate)
            db.session.commit()
            
            flash(f'Candidate "{candidate.name}" added successfully!', 'success')
            return redirect(url_for('admin.view_candidates'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding candidate: {e}')
            flash('An error occurred while adding the candidate.', 'danger')
    
    return render_template('admin/add_candidate.html', form=form)


@admin_bp.route('/candidates')
@login_required
@admin_required
def view_candidates():
    """View all candidates."""
    candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
    return render_template('admin/candidates.html', candidates=candidates)


@admin_bp.route('/delete-candidate/<int:id>')
@login_required
@admin_required
def delete_candidate(id):
    """
    Delete a candidate.
    
    Args:
        id: Candidate ID to delete
    """
    candidate = Candidate.query.get_or_404(id)
    
    try:
        db.session.delete(candidate)
        db.session.commit()
        flash(f'Candidate "{candidate.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting candidate: {e}')
        flash('An error occurred while deleting the candidate.', 'danger')
    
    return redirect(url_for('admin.view_candidates'))


@admin_bp.route('/toggle-candidate/<int:id>')
@login_required
@admin_required
def toggle_candidate(id):
    """
    Toggle candidate active status.
    
    Args:
        id: Candidate ID to toggle
    """
    candidate = Candidate.query.get_or_404(id)
    
    try:
        candidate.is_active = not candidate.is_active
        db.session.commit()
        
        status = 'activated' if candidate.is_active else 'deactivated'
        flash(f'Candidate "{candidate.name}" {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling candidate: {e}')
        flash('An error occurred while updating the candidate.', 'danger')
    
    return redirect(url_for('admin.view_candidates'))


@admin_bp.route('/voters')
@login_required
@admin_required
def view_voters():
    """View all registered voters."""
    # Get filter parameters
    verified = request.args.get('verified')
    search = request.args.get('search')
    
    query = User.query.filter_by(role='voter')
    
    if verified == 'true':
        query = query.filter_by(is_verified=True)
    elif verified == 'false':
        query = query.filter_by(is_verified=False)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search))
        )
    
    voters = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/view_voters.html', voters=voters)


@admin_bp.route('/voter/<int:id>')
@login_required
@admin_required
def view_voter_detail(id):
    """View voter details."""
    voter = User.query.get_or_404(id)
    vote = Vote.query.filter_by(voter_id=id).first()
    
    return render_template('admin/voter_detail.html', voter=voter, vote=vote)


@admin_bp.route('/results')
@login_required
@admin_required
def results():
    """View voting results."""
    # Get all active candidates with vote counts
    candidates = Candidate.query.filter_by(is_active=True).all()
    
    results = []
    for candidate in candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results.append({
            'candidate': candidate,
            'vote_count': vote_count
        })
    
    # Sort by vote count
    results.sort(key=lambda x: x['vote_count'], reverse=True)
    
    # Get total votes
    total_votes = Vote.query.count()
    
    # Get election settings
    election = ElectionSettings.query.first()
    
    return render_template(
        'admin/results.html',
        results=results,
        total_votes=total_votes,
        election=election
    )


@admin_bp.route('/election-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def election_settings():
    """Configure election settings."""
    election = ElectionSettings.query.first()
    
    if not election:
        election = ElectionSettings()
        db.session.add(election)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            election.election_name = request.form.get('election_name')
            election.election_description = request.form.get('election_description')
            election.is_active = 'is_active' in request.form
            
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
            if start_date:
                election.start_date = datetime.fromisoformat(start_date)
            if end_date:
                election.end_date = datetime.fromisoformat(end_date)
            
            db.session.commit()
            flash('Election settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating election settings: {e}')
            flash('An error occurred while updating settings.', 'danger')
    
    return render_template('admin/election_settings.html', election=election)


# =============================================================================
# API Routes
# =============================================================================

@admin_bp.route('/api/results')
@login_required
@admin_required
def api_results():
    """API endpoint for voting results."""
    candidates = Candidate.query.filter_by(is_active=True).all()
    
    results = []
    for candidate in candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results.append({
            'id': candidate.id,
            'name': candidate.name,
            'party': candidate.party,
            'vote_count': vote_count
        })
    
    results.sort(key=lambda x: x['vote_count'], reverse=True)
    
    return jsonify({
        'results': results,
        'total_votes': Vote.query.count()
    }), 200


@admin_bp.route('/api/voters')
@login_required
@admin_required
def api_voters():
    """API endpoint for voter list."""
    voters = User.query.filter_by(role='voter').all()
    
    return jsonify({
        'voters': [v.to_dict() for v in voters]
    }), 200
