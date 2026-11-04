import os
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, session, abort, current_app
from sqlalchemy import func, desc
from app.admin import admin_bp
from app.extensions import db
from app.models import Game, Genre, Platform, User, Review, ReviewComment, Rating, Like, Wishlist, Activity, slugify
from app.utils.decorators import admin_required
from app.utils.helpers import save_uploaded_image

@admin_bp.before_request
@admin_required
def check_admin():
    pass


@admin_bp.route('/')
def overview():
    total_games = Game.query.count()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    total_ratings = Rating.query.count()
    total_likes = Like.query.count()
    
    # Calculate global average rating
    avg_rating_row = db.session.query(func.avg(Rating.score)).scalar()
    global_avg_rating = round(float(avg_rating_row), 1) if avg_rating_row else 0.0

    recent_games = Game.query.order_by(desc(Game.created_at)).limit(5).all()
    recent_reviews = Review.query.order_by(desc(Review.created_at)).limit(5).all()
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()

    return render_template(
        'admin/overview.html',
        total_games=total_games,
        total_users=total_users,
        total_reviews=total_reviews,
        total_ratings=total_ratings,
        total_likes=total_likes,
        global_avg_rating=global_avg_rating,
        recent_games=recent_games,
        recent_reviews=recent_reviews,
        recent_users=recent_users
    )


# ================= G A M E S =================

@admin_bp.route('/games')
def manage_games():
    search = request.args.get('q', '').strip()
    query = Game.query
    if search:
        query = query.filter(Game.title.ilike(f'%{search}%'))
    games = query.order_by(desc(Game.created_at)).all()
    return render_template('admin/games.html', games=games, search=search)


@admin_bp.route('/games/add', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        developer = request.form.get('developer', '').strip()
        publisher = request.form.get('publisher', '').strip()
        game_mode = request.form.get('game_mode', 'Single-player')
        release_date_str = request.form.get('release_date', '').strip()
        
        genre_ids = request.form.getlist('genre_ids', type=int)
        platform_ids = request.form.getlist('platform_ids', type=int)

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return redirect(url_for('admin.add_game'))

        # Unique slug generation
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Game.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Release date parsing
        release_date = None
        if release_date_str:
            try:
                release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Handle Cover Upload (mandatory for new game)
        cover_file = request.files.get('cover_image')
        cover_filename = None
        if cover_file and cover_file.filename != '':
            try:
                cover_filename = save_uploaded_image(cover_file, folder_name='covers', max_size=(800, 1100))
            except Exception as e:
                flash(f"Cover upload error: {str(e)}", 'danger')
                return redirect(url_for('admin.add_game'))
        else:
            flash('Please upload a cover image for the game.', 'danger')
            return redirect(url_for('admin.add_game'))

        # Handle Banner Upload (optional)
        banner_file = request.files.get('banner_image')
        banner_filename = None
        if banner_file and banner_file.filename != '':
            try:
                banner_filename = save_uploaded_image(banner_file, folder_name='banners', max_size=(1920, 1080))
            except Exception as e:
                flash(f"Banner upload error: {str(e)}", 'warning')

        game = Game(
            title=title,
            slug=slug,
            description=description,
            developer=developer or None,
            publisher=publisher or None,
            game_mode=game_mode,
            release_date=release_date,
            cover_image=cover_filename,
            banner_image=banner_filename
        )

        if genre_ids:
            game.genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
        if platform_ids:
            game.platforms = Platform.query.filter(Platform.id.in_(platform_ids)).all()

        db.session.add(game)
        db.session.commit()

        flash(f'Game "{game.title}" was added successfully!', 'success')
        return redirect(url_for('admin.manage_games'))

    genres = Genre.query.order_by(Genre.name).all()
    platforms = Platform.query.order_by(Platform.name).all()
    return render_template('admin/game_form.html', game=None, genres=genres, platforms=platforms)


@admin_bp.route('/games/<int:game_id>/edit', methods=['GET', 'POST'])
def edit_game(game_id):
    game = Game.query.get_or_404(game_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        developer = request.form.get('developer', '').strip()
        publisher = request.form.get('publisher', '').strip()
        game_mode = request.form.get('game_mode', 'Single-player')
        release_date_str = request.form.get('release_date', '').strip()
        
        genre_ids = request.form.getlist('genre_ids', type=int)
        platform_ids = request.form.getlist('platform_ids', type=int)

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return redirect(url_for('admin.edit_game', game_id=game.id))

        # Check slug if title changed
        if title != game.title:
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Game.query.filter(Game.slug == slug, Game.id != game.id).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            game.slug = slug
            game.title = title

        game.description = description
        game.developer = developer or None
        game.publisher = publisher or None
        game.game_mode = game_mode

        # Parse release date
        if release_date_str:
            try:
                game.release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
            except ValueError:
                game.release_date = None
        else:
            game.release_date = None

        # Cover upload update
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename != '':
            try:
                new_cover = save_uploaded_image(cover_file, folder_name='covers', max_size=(800, 1100))
                if new_cover:
                    game.cover_image = new_cover
            except Exception as e:
                flash(f"Cover upload error: {str(e)}", 'danger')

        # Banner upload update
        banner_file = request.files.get('banner_image')
        if banner_file and banner_file.filename != '':
            try:
                new_banner = save_uploaded_image(banner_file, folder_name='banners', max_size=(1920, 1080))
                if new_banner:
                    game.banner_image = new_banner
            except Exception as e:
                flash(f"Banner upload error: {str(e)}", 'warning')

        game.genres = Genre.query.filter(Genre.id.in_(genre_ids)).all() if genre_ids else []
        game.platforms = Platform.query.filter(Platform.id.in_(platform_ids)).all() if platform_ids else []

        db.session.commit()
        flash(f'Game "{game.title}" updated successfully!', 'success')
        return redirect(url_for('admin.manage_games'))

    genres = Genre.query.order_by(Genre.name).all()
    platforms = Platform.query.order_by(Platform.name).all()
    return render_template('admin/game_form.html', game=game, genres=genres, platforms=platforms)


@admin_bp.route('/games/<int:game_id>/delete', methods=['POST'])
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    title = game.title
    db.session.delete(game)
    db.session.commit()
    flash(f'Game "{title}" has been deleted.', 'info')
    return redirect(url_for('admin.manage_games'))


# ================= G E N R E S =================

@admin_bp.route('/genres', methods=['GET', 'POST'])
def manage_genres():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            if not name:
                flash('Genre name cannot be empty.', 'danger')
            elif Genre.query.filter_by(name=name).first():
                flash('A genre with this name already exists.', 'warning')
            else:
                genre = Genre(name=name, description=description)
                db.session.add(genre)
                db.session.commit()
                flash(f'Genre "{genre.name}" created.', 'success')

        elif action == 'edit':
            genre_id = request.form.get('genre_id', type=int)
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            genre = Genre.query.get_or_404(genre_id)
            if not name:
                flash('Genre name cannot be empty.', 'danger')
            else:
                genre.name = name
                genre.description = description
                genre.slug = slugify(name)
                db.session.commit()
                flash('Genre updated successfully.', 'success')

        elif action == 'delete':
            genre_id = request.form.get('genre_id', type=int)
            genre = Genre.query.get_or_404(genre_id)
            db.session.delete(genre)
            db.session.commit()
            flash('Genre deleted.', 'info')

        return redirect(url_for('admin.manage_genres'))

    genres = Genre.query.order_by(Genre.name).all()
    return render_template('admin/genres.html', genres=genres)


# ================= P L A T F O R M S =================

@admin_bp.route('/platforms', methods=['GET', 'POST'])
def manage_platforms():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            icon_class = request.form.get('icon_class', 'bi-controller').strip()
            if not name:
                flash('Platform name cannot be empty.', 'danger')
            elif Platform.query.filter_by(name=name).first():
                flash('A platform with this name already exists.', 'warning')
            else:
                platform = Platform(name=name, icon_class=icon_class)
                db.session.add(platform)
                db.session.commit()
                flash(f'Platform "{platform.name}" created.', 'success')

        elif action == 'edit':
            platform_id = request.form.get('platform_id', type=int)
            name = request.form.get('name', '').strip()
            icon_class = request.form.get('icon_class', 'bi-controller').strip()
            platform = Platform.query.get_or_404(platform_id)
            if not name:
                flash('Platform name cannot be empty.', 'danger')
            else:
                platform.name = name
                platform.icon_class = icon_class
                platform.slug = slugify(name)
                db.session.commit()
                flash('Platform updated successfully.', 'success')

        elif action == 'delete':
            platform_id = request.form.get('platform_id', type=int)
            platform = Platform.query.get_or_404(platform_id)
            db.session.delete(platform)
            db.session.commit()
            flash('Platform deleted.', 'info')

        return redirect(url_for('admin.manage_platforms'))

    platforms = Platform.query.order_by(Platform.name).all()
    return render_template('admin/platforms.html', platforms=platforms)


# ================= U S E R S =================

@admin_bp.route('/users')
def manage_users():
    search = request.args.get('q', '').strip()
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    users = query.order_by(desc(User.created_at)).all()
    return render_template('admin/users.html', users=users, search=search)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot deactivate your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    flash(f'User "{user.username}" has been {status_str}.', 'info')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
def toggle_user_role(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user = User.query.get_or_404(user_id)
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f'User "{user.username}" role updated to {user.role}.', 'success')
    return redirect(url_for('admin.manage_users'))


# ================= R E V I E W S  M O D E R A T I O N =================

@admin_bp.route('/reviews')
def manage_reviews():
    filter_mode = request.args.get('filter', 'all')
    query = Review.query
    if filter_mode == 'flagged':
        query = query.filter_by(is_flagged=True)
    reviews = query.order_by(desc(Review.created_at)).all()
    comments = ReviewComment.query.order_by(desc(ReviewComment.created_at)).limit(20).all()
    return render_template('admin/reviews.html', reviews=reviews, comments=comments, filter_mode=filter_mode)


# ================= S T A T I S T I C S =================

@admin_bp.route('/statistics')
def statistics():
    total_games = Game.query.count()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    total_ratings = Rating.query.count()
    total_likes = Like.query.count()
    total_wishlists = Wishlist.query.count()

    # Games per genre
    genres_data = []
    for g in Genre.query.all():
        genres_data.append({
            'name': g.name,
            'count': len(g.games)
        })

    # Games per platform
    platforms_data = []
    for p in Platform.query.all():
        platforms_data.append({
            'name': p.name,
            'count': len(p.games)
        })

    # Top 5 highest rated games
    top_rated = Game.query.filter(Game.total_ratings > 0).order_by(desc(Game.average_rating), desc(Game.total_ratings)).limit(5).all()

    # Top 5 most reviewed games
    most_reviewed = db.session.query(
        Game, func.count(Review.id).label('review_count')
    ).join(Review, Game.id == Review.game_id).group_by(Game.id).order_by(desc('review_count')).limit(5).all()

    # Top 5 most liked games
    most_liked = db.session.query(
        Game, func.count(Like.id).label('like_count')
    ).join(Like, Game.id == Like.game_id).group_by(Game.id).order_by(desc('like_count')).limit(5).all()

    return render_template(
        'admin/statistics.html',
        total_games=total_games,
        total_users=total_users,
        total_reviews=total_reviews,
        total_ratings=total_ratings,
        total_likes=total_likes,
        total_wishlists=total_wishlists,
        genres_data=genres_data,
        platforms_data=platforms_data,
        top_rated=top_rated,
        most_reviewed=most_reviewed,
        most_liked=most_liked
    )

