from flask import render_template, request, flash, redirect, url_for, session, abort
from app.reviews import reviews_bp
from app.extensions import db
from app.models import Review, ReviewComment, Game, Rating, User
from app.utils.decorators import login_required
from app.utils.helpers import log_activity, create_notification

@reviews_bp.route('/games/<int:game_id>/reviews', methods=['POST'])
@login_required
def create_review(game_id):
    game = Game.query.get_or_404(game_id)
    user_id = session['user_id']
    user = User.query.get(user_id)

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    rating_score = request.form.get('rating_score', type=int)

    if not content:
        flash('Review text cannot be empty.', 'danger')
        return redirect(url_for('games.detail', slug=game.slug))

    # Check if user already reviewed this game
    existing_review = Review.query.filter_by(user_id=user_id, game_id=game.id).first()
    if existing_review:
        flash('You have already submitted a review for this game. You can edit your existing review.', 'warning')
        return redirect(url_for('games.detail', slug=game.slug))

    # If rating score provided, record/update rating
    if rating_score and 1 <= rating_score <= 5:
        rating = Rating.query.filter_by(user_id=user_id, game_id=game.id).first()
        if rating:
            rating.score = rating_score
        else:
            rating = Rating(user_id=user_id, game_id=game.id, score=rating_score)
            db.session.add(rating)
        db.session.commit()
        game.recalculate_rating()

    # Create review
    review = Review(
        user_id=user_id,
        game_id=game.id,
        title=title if title else None,
        content=content,
        rating_score=rating_score or game.get_user_rating(user_id)
    )
    db.session.add(review)
    db.session.commit()

    log_activity(user_id, 'reviewed', game.id, f"wrote a review for {game.title}")
    flash('Your review has been published successfully!', 'success')
    return redirect(url_for('games.detail', slug=game.slug))


@reviews_bp.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    user_id = session['user_id']

    if review.user_id != user_id and session.get('role') != 'admin':
        abort(403)

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    rating_score = request.form.get('rating_score', type=int)

    if not content:
        flash('Review content cannot be empty.', 'danger')
        return redirect(url_for('games.detail', slug=review.game.slug))

    review.title = title if title else None
    review.content = content

    if rating_score and 1 <= rating_score <= 5:
        review.rating_score = rating_score
        rating = Rating.query.filter_by(user_id=review.user_id, game_id=review.game_id).first()
        if rating:
            rating.score = rating_score
        else:
            rating = Rating(user_id=review.user_id, game_id=review.game_id, score=rating_score)
            db.session.add(rating)
        db.session.commit()
        review.game.recalculate_rating()

    db.session.commit()
    flash('Review updated successfully.', 'success')
    return redirect(url_for('games.detail', slug=review.game.slug))


@reviews_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    user_id = session['user_id']
    is_admin = session.get('role') == 'admin'

    if review.user_id != user_id and not is_admin:
        abort(403)

    game_slug = review.game.slug
    db.session.delete(review)
    db.session.commit()

    flash('Review deleted successfully.', 'info')
    
    # If admin initiated from admin dashboard, redirect there
    if is_admin and request.referrer and '/admin/reviews' in request.referrer:
        return redirect(url_for('admin.manage_reviews'))
        
    return redirect(url_for('games.detail', slug=game_slug))


@reviews_bp.route('/reviews/<int:review_id>/comments', methods=['POST'])
@login_required
def add_comment(review_id):
    review = Review.query.get_or_404(review_id)
    user_id = session['user_id']
    username = session.get('username')
    content = request.form.get('content', '').strip()

    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('games.detail', slug=review.game.slug))

    comment = ReviewComment(
        review_id=review.id,
        user_id=user_id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()

    # Notify the review author
    notification_msg = f"{username} commented on your review of {review.game.title}."
    detail_link = url_for('games.detail', slug=review.game.slug) + f"#review-{review.id}"
    create_notification(review.user_id, user_id, 'comment', notification_msg, detail_link)

    log_activity(user_id, 'commented', review.game_id, f"commented on a review for {review.game.title}")
    flash('Comment posted!', 'success')
    return redirect(url_for('games.detail', slug=review.game.slug) + f"#review-{review.id}")


@reviews_bp.route('/reviews/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = ReviewComment.query.get_or_404(comment_id)
    user_id = session['user_id']
    is_admin = session.get('role') == 'admin'

    if comment.user_id != user_id and not is_admin:
        abort(403)

    game_slug = comment.review.game.slug
    review_id = comment.review.id
    db.session.delete(comment)
    db.session.commit()

    flash('Comment deleted.', 'info')
    
    if is_admin and request.referrer and '/admin/reviews' in request.referrer:
        return redirect(url_for('admin.manage_reviews'))
        
    return redirect(url_for('games.detail', slug=game_slug) + f"#review-{review_id}")

