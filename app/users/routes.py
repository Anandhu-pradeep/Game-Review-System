import os
from flask import render_template, request, flash, redirect, url_for, session, abort, current_app
from app.users import users_bp
from app.extensions import db
from app.models import User, Review, Rating, Wishlist, Like, Activity, Notification
from app.utils.decorators import login_required
from app.utils.helpers import save_uploaded_image, log_activity

@users_bp.route('/users/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not user.is_active:
        flash("This user's profile is currently suspended.", "warning")
        return redirect(url_for('games.index'))

    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).limit(10).all()
    ratings = Rating.query.filter_by(user_id=user.id).order_by(Rating.created_at.desc()).limit(10).all()
    wishlist_items = Wishlist.query.filter_by(user_id=user.id).order_by(Wishlist.created_at.desc()).all()
    likes = Like.query.filter_by(user_id=user.id).order_by(Like.created_at.desc()).limit(12).all()
    recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).limit(15).all()

    return render_template(
        'users/public_profile.html',
        profile_user=user,
        reviews=reviews,
        ratings=ratings,
        wishlist_items=wishlist_items,
        likes=likes,
        activities=recent_activities
    )


@users_bp.route('/profile')
@login_required
def my_profile():
    user = User.query.get(session['user_id'])
    reviews_count = Review.query.filter_by(user_id=user.id).count()
    ratings_count = Rating.query.filter_by(user_id=user.id).count()
    wishlist_count = Wishlist.query.filter_by(user_id=user.id).count()
    likes_count = Like.query.filter_by(user_id=user.id).count()
    recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).limit(10).all()
    recent_reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).limit(5).all()

    return render_template(
        'users/profile.html',
        user=user,
        reviews_count=reviews_count,
        ratings_count=ratings_count,
        wishlist_count=wishlist_count,
        likes_count=likes_count,
        activities=recent_activities,
        recent_reviews=recent_reviews
    )


@users_bp.route('/my-reviews')
@login_required
def my_reviews():
    user = User.query.get(session['user_id'])
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).all()
    return render_template('users/reviews.html', user=user, reviews=reviews)


@users_bp.route('/my-ratings')
@login_required
def my_ratings():
    user = User.query.get(session['user_id'])
    ratings = Rating.query.filter_by(user_id=user.id).order_by(Rating.created_at.desc()).all()
    return render_template('users/ratings.html', user=user, ratings=ratings)


@users_bp.route('/my-wishlist')
@login_required
def my_wishlist():
    user = User.query.get(session['user_id'])
    wishlist_items = Wishlist.query.filter_by(user_id=user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template('users/wishlist.html', user=user, wishlist_items=wishlist_items)


@users_bp.route('/my-activity')
@login_required
def my_activity():
    user = User.query.get(session['user_id'])
    activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).all()
    return render_template('users/activity.html', user=user, activities=activities)


@users_bp.route('/notifications')
@login_required
def notifications():
    user = User.query.get(session['user_id'])
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template('users/notifications.html', user=user, notifications=notifs)


@users_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=session['user_id']).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for('users.notifications'))


@users_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('users.notifications'))


@users_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        action = request.form.get('action')

        # Update Profile Info (Bio & Email)
        if action == 'update_profile':
            bio = request.form.get('bio', '').strip()
            email = request.form.get('email', '').strip().lower()

            if email and email != user.email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    flash('That email address is already in use by another account.', 'danger')
                    return redirect(url_for('users.settings'))
                user.email = email

            user.bio = bio
            
            # Handle Avatar Upload
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename != '':
                    try:
                        filename = save_uploaded_image(file, folder_name='avatars', max_size=(400, 400))
                        if filename:
                            user.avatar = filename
                    except Exception as e:
                        flash(f"Avatar upload failed: {str(e)}", 'danger')
                        return redirect(url_for('users.settings'))

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('users.settings'))

        # Change Password
        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('users.settings'))

            if not new_password or len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
                return redirect(url_for('users.settings'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('users.settings'))

            user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('users.settings'))

    return render_template('users/settings.html', user=user)

