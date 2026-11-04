from flask import render_template, request, jsonify, flash, redirect, url_for, session, abort
from sqlalchemy import func, desc, asc
from app.games import games_bp
from app.extensions import db
from app.models import Game, Genre, Platform, Rating, Review, Like, Wishlist, User
from app.utils.decorators import login_required
from app.utils.helpers import log_activity, create_notification

@games_bp.route('/')
def index():
    # Hero / featured games carousel - prefer Spider-Man as #1 to match reference
    spiderman = Game.query.filter(Game.title.ilike('%Spider-Man%')).first()
    other_featured = Game.query.filter(Game.title.notilike('%Spider-Man%')).order_by(desc(Game.average_rating), desc(Game.total_ratings)).limit(4).all()
    
    if spiderman:
        carousel_games = [spiderman] + other_featured
    else:
        carousel_games = Game.query.order_by(desc(Game.average_rating), desc(Game.total_ratings)).limit(5).all()
        
    featured_game = carousel_games[0] if carousel_games else None

    # In Library games (wishlisted by user, or curated library showcase)
    in_library_games = []
    if 'user_id' in session:
        user_wishlist = Wishlist.query.filter_by(user_id=session['user_id']).order_by(desc(Wishlist.created_at)).limit(4).all()
        in_library_games = [w.game for w in user_wishlist if w.game]
    
    if not in_library_games:
        # Showcase games for the In Library panel (Clash, NFS, Ghost, Overwatch)
        fav_titles = ['%Clash%', '%NFS%', '%Ghost%', '%Overwatch%']
        for pat in fav_titles:
            g = Game.query.filter(Game.title.ilike(pat)).first()
            if g and g not in in_library_games:
                in_library_games.append(g)
        # If still less than 4, fill with other games
        if len(in_library_games) < 4:
            more_games = Game.query.filter(~Game.id.in_([g.id for g in in_library_games] if in_library_games else [0])).limit(4 - len(in_library_games)).all()
            in_library_games.extend(more_games)

    # You Might Also Like games (Apex, Overwatch, Marvel Rivals, Street Fighter)
    recom_titles = ['%Apex%', '%Overwatch%', '%Marvel Rivals%', '%Street Fighter%']
    you_might_like = []
    for pat in recom_titles:
        g = Game.query.filter(Game.title.ilike(pat)).first()
        if g and g not in you_might_like:
            you_might_like.append(g)
    if len(you_might_like) < 4:
        extra = Game.query.filter(~Game.id.in_([g.id for g in you_might_like] if you_might_like else [0])).limit(4 - len(you_might_like)).all()
        you_might_like.extend(extra)

    # Trending / Popular games
    trending_games = Game.query.order_by(desc(Game.total_ratings), desc(Game.average_rating)).limit(6).all()
    
    # Highest rated games
    highest_rated = Game.query.filter(Game.total_ratings >= 1).order_by(desc(Game.average_rating), desc(Game.total_ratings)).limit(6).all()
    if not highest_rated:
        highest_rated = Game.query.order_by(desc(Game.average_rating)).limit(6).all()
        
    # Recently added games
    recent_games = Game.query.order_by(desc(Game.created_at)).limit(6).all()
    
    # Genres with game counts
    genres = Genre.query.all()
    
    # Quick platform stats
    total_games = Game.query.count()
    total_reviews = Review.query.count()
    total_users = User.query.filter_by(is_active=True).count()
    
    # Community reviews
    community_reviews = Review.query.order_by(desc(Review.created_at)).limit(3).all()
    popular_this_week = Game.query.order_by(desc(Game.total_ratings), desc(Game.created_at)).limit(4).all()
    
    return render_template(
        'index.html',
        featured_game=featured_game,
        carousel_games=carousel_games,
        in_library_games=in_library_games,
        you_might_like=you_might_like,
        trending_games=trending_games,
        highest_rated=highest_rated,
        recent_games=recent_games,
        genres=genres,
        total_games=total_games,
        total_reviews=total_reviews,
        total_users=total_users,
        community_reviews=community_reviews,
        popular_this_week=popular_this_week
    )


@games_bp.route('/games')
def catalogue():
    search_query = request.args.get('q', '').strip()
    genre_slug = request.args.get('genre', '').strip()
    platform_slug = request.args.get('platform', '').strip()
    game_mode = request.args.get('mode', '').strip()
    sort_by = request.args.get('sort', 'popular').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Game.query

    # Search filter
    if search_query:
        query = query.filter(
            (Game.title.ilike(f'%{search_query}%')) |
            (Game.description.ilike(f'%{search_query}%')) |
            (Game.developer.ilike(f'%{search_query}%')) |
            (Game.publisher.ilike(f'%{search_query}%'))
        )

    # Genre filter
    if genre_slug:
        query = query.join(Game.genres).filter(Genre.slug == genre_slug)

    # Platform filter
    if platform_slug:
        query = query.join(Game.platforms).filter(Platform.slug == platform_slug)

    # Mode filter
    if game_mode and game_mode in ['Single-player', 'Multiplayer', 'Both']:
        query = query.filter(Game.game_mode == game_mode)

    # Sorting
    if sort_by == 'rating':
        query = query.order_by(desc(Game.average_rating), desc(Game.total_ratings))
    elif sort_by == 'newest':
        query = query.order_by(desc(Game.release_date.nullslast()), desc(Game.created_at))
    elif sort_by == 'az':
        query = query.order_by(asc(Game.title))
    elif sort_by == 'za':
        query = query.order_by(desc(Game.title))
    else:  # 'popular'
        query = query.order_by(desc(Game.total_ratings), desc(Game.average_rating), desc(Game.created_at))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    games = pagination.items

    all_genres = Genre.query.order_by(Genre.name).all()
    all_platforms = Platform.query.order_by(Platform.name).all()

    return render_template(
        'games/catalogue.html',
        games=games,
        pagination=pagination,
        search_query=search_query,
        selected_genre=genre_slug,
        selected_platform=platform_slug,
        selected_mode=game_mode,
        selected_sort=sort_by,
        all_genres=all_genres,
        all_platforms=all_platforms
    )


@games_bp.route('/games/<slug>')
def detail(slug):
    game = Game.query.filter_by(slug=slug).first_or_404()
    user_id = session.get('user_id')

    # Sorting for reviews
    review_sort = request.args.get('sort', 'newest').strip()
    reviews_query = Review.query.filter_by(game_id=game.id)
    
    if review_sort == 'oldest':
        reviews_query = reviews_query.order_by(asc(Review.created_at))
    elif review_sort == 'highest-rated':
        reviews_query = reviews_query.order_by(desc(Review.rating_score.nullslast()), desc(Review.created_at))
    else:  # newest
        reviews_query = reviews_query.order_by(desc(Review.created_at))
        
    reviews = reviews_query.all()

    # User interactions
    user_rating = 0
    is_liked = False
    is_wishlisted = False
    user_review = None

    if user_id:
        user_rating = game.get_user_rating(user_id)
        is_liked = game.is_liked_by(user_id)
        is_wishlisted = game.is_wishlisted_by(user_id)
        user_review = Review.query.filter_by(game_id=game.id, user_id=user_id).first()

    # Similar games (by first genre)
    similar_games = []
    if game.genres:
        similar_games = Game.query.join(Game.genres).filter(
            Genre.id == game.genres[0].id,
            Game.id != game.id
        ).limit(4).all()

    return render_template(
        'games/detail.html',
        game=game,
        reviews=reviews,
        user_rating=user_rating,
        is_liked=is_liked,
        is_wishlisted=is_wishlisted,
        user_review=user_review,
        similar_games=similar_games,
        current_sort=review_sort
    )


@games_bp.route('/games/<int:game_id>/rate', methods=['POST'])
@login_required
def rate_game(game_id):
    game = Game.query.get_or_404(game_id)
    user_id = session['user_id']
    
    score = request.form.get('score', type=int)
    if not score or score < 1 or score > 5:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5 stars.'}), 400
        flash('Rating must be between 1 and 5 stars.', 'danger')
        return redirect(url_for('games.detail', slug=game.slug))

    # Check if rating exists
    rating = Rating.query.filter_by(user_id=user_id, game_id=game.id).first()
    is_new = False
    if rating:
        rating.score = score
    else:
        rating = Rating(user_id=user_id, game_id=game.id, score=score)
        db.session.add(rating)
        is_new = True

    db.session.commit()
    game.recalculate_rating()
    db.session.commit()

    action_text = f"rated {game.title} with {score} stars"
    log_activity(user_id, 'rated', game.id, action_text)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': 'Rating saved successfully!',
            'score': score,
            'average_rating': game.average_rating,
            'total_ratings': game.total_ratings
        })

    flash('Your rating has been saved!', 'success')
    return redirect(url_for('games.detail', slug=game.slug))


@games_bp.route('/games/<int:game_id>/like', methods=['POST'])
@login_required
def toggle_like(game_id):
    game = Game.query.get_or_404(game_id)
    user_id = session['user_id']

    existing_like = Like.query.filter_by(user_id=user_id, game_id=game.id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        liked = False
        message = f"Removed {game.title} from liked games."
    else:
        new_like = Like(user_id=user_id, game_id=game.id)
        db.session.add(new_like)
        db.session.commit()
        liked = True
        message = f"Added {game.title} to liked games."
        log_activity(user_id, 'liked', game.id, f"liked {game.title}")

    likes_count = Like.query.filter_by(game_id=game.id).count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': likes_count,
            'message': message
        })

    flash(message, 'info')
    return redirect(url_for('games.detail', slug=game.slug))


@games_bp.route('/games/<int:game_id>/wishlist', methods=['POST'])
@login_required
def toggle_wishlist(game_id):
    game = Game.query.get_or_404(game_id)
    user_id = session['user_id']

    existing = Wishlist.query.filter_by(user_id=user_id, game_id=game.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        in_wishlist = False
        message = f"Removed {game.title} from your wishlist."
    else:
        new_item = Wishlist(user_id=user_id, game_id=game.id)
        db.session.add(new_item)
        db.session.commit()
        in_wishlist = True
        message = f"Added {game.title} to your wishlist!"
        log_activity(user_id, 'wishlisted', game.id, f"added {game.title} to wishlist")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': message
        })

    flash(message, 'info')
    return redirect(url_for('games.detail', slug=game.slug))

