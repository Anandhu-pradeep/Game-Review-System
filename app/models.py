from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

# Many-to-Many Association Tables
game_genres = db.Table(
    'game_genres',
    db.Column('game_id', db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

game_platforms = db.Table(
    'game_platforms',
    db.Column('game_id', db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), primary_key=True),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    bio = db.Column(db.Text, nullable=True, default='')
    avatar = db.Column(db.String(255), nullable=False, default='default_avatar.png')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    ratings = db.relationship('Rating', back_populates='user', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')
    review_comments = db.relationship('ReviewComment', back_populates='user', cascade='all, delete-orphan')
    likes = db.relationship('Like', back_populates='user', cascade='all, delete-orphan')
    wishlists = db.relationship('Wishlist', back_populates='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', foreign_keys='Notification.user_id', back_populates='recipient', cascade='all, delete-orphan')
    activities = db.relationship('Activity', back_populates='user', cascade='all, delete-orphan', order_by='desc(Activity.created_at)')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    games = db.relationship('Game', secondary=game_genres, back_populates='genres')

    def __init__(self, name, description=None, slug=None):
        self.name = name
        self.description = description
        self.slug = slug or slugify(name)

    def __repr__(self):
        return f'<Genre {self.name}>'


class Platform(db.Model):
    __tablename__ = 'platforms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    icon_class = db.Column(db.String(50), nullable=True, default='bi-controller')

    games = db.relationship('Game', secondary=game_platforms, back_populates='platforms')

    def __init__(self, name, icon_class=None, slug=None):
        self.name = name
        self.icon_class = icon_class or 'bi-controller'
        self.slug = slug or slugify(name)

    def __repr__(self):
        return f'<Platform {self.name}>'


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(255), nullable=False)
    banner_image = db.Column(db.String(255), nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    developer = db.Column(db.String(100), nullable=True)
    publisher = db.Column(db.String(100), nullable=True)
    game_mode = db.Column(db.String(50), default='Single-player', nullable=False)  # Single-player, Multiplayer, Both
    average_rating = db.Column(db.Float, default=0.0, nullable=False)
    total_ratings = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    genres = db.relationship('Genre', secondary=game_genres, back_populates='games')
    platforms = db.relationship('Platform', secondary=game_platforms, back_populates='games')
    ratings = db.relationship('Rating', back_populates='game', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='game', cascade='all, delete-orphan', order_by='desc(Review.created_at)')
    likes = db.relationship('Like', back_populates='game', cascade='all, delete-orphan')
    wishlists = db.relationship('Wishlist', back_populates='game', cascade='all, delete-orphan')

    def recalculate_rating(self):
        rating_list = [r.score for r in self.ratings]
        if rating_list:
            self.total_ratings = len(rating_list)
            self.average_rating = round(sum(rating_list) / len(rating_list), 1)
        else:
            self.total_ratings = 0
            self.average_rating = 0.0

    def is_liked_by(self, user_id):
        if not user_id:
            return False
        return Like.query.filter_by(game_id=self.id, user_id=user_id).first() is not None

    def is_wishlisted_by(self, user_id):
        if not user_id:
            return False
        return Wishlist.query.filter_by(game_id=self.id, user_id=user_id).first() is not None

    def get_user_rating(self, user_id):
        if not user_id:
            return 0
        r = Rating.query.filter_by(game_id=self.id, user_id=user_id).first()
        return r.score if r else 0

    @property
    def likes_count(self):
        return len(self.likes)

    def __repr__(self):
        return f'<Game {self.title}>'


class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 1 to 5
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id', name='uq_user_game_rating'),
        db.CheckConstraint('score >= 1 AND score <= 5', name='chk_score_range'),
    )

    user = db.relationship('User', back_populates='ratings')
    game = db.relationship('Game', back_populates='ratings')

    def __repr__(self):
        return f'<Rating user:{self.user_id} game:{self.game_id} score:{self.score}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(120), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating_score = db.Column(db.Integer, nullable=True)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='reviews')
    game = db.relationship('Game', back_populates='reviews')
    comments = db.relationship('ReviewComment', back_populates='review', cascade='all, delete-orphan', order_by='ReviewComment.created_at.asc()')

    @property
    def author(self):
        return self.user

    def __repr__(self):
        return f'<Review {self.id} by User {self.user_id} on Game {self.game_id}>'


class ReviewComment(db.Model):
    __tablename__ = 'review_comments'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    review = db.relationship('Review', back_populates='comments')
    user = db.relationship('User', back_populates='review_comments')

    def __repr__(self):
        return f'<ReviewComment {self.id} by User {self.user_id}>'


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id', name='uq_user_game_like'),
    )

    user = db.relationship('User', back_populates='likes')
    game = db.relationship('Game', back_populates='likes')

    def __repr__(self):
        return f'<Like user:{self.user_id} game:{self.game_id}>'


class Wishlist(db.Model):
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id', name='uq_user_game_wishlist'),
    )

    user = db.relationship('User', back_populates='wishlists')
    game = db.relationship('Game', back_populates='wishlists')

    def __repr__(self):
        return f'<Wishlist user:{self.user_id} game:{self.game_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # Recipient
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)  # Triggered by
    type = db.Column(db.String(50), nullable=False)  # 'comment', 'like', 'system', 'review'
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    recipient = db.relationship('User', foreign_keys=[user_id], back_populates='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])

    def __repr__(self):
        return f'<Notification to {self.user_id}: {self.message}>'


class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'rated', 'reviewed', 'liked', 'wishlisted', 'commented'
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='activities')
    game = db.relationship('Game')

    def __repr__(self):
        return f'<Activity {self.user_id}: {self.activity_type}>'

