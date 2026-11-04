from flask import Blueprint

games_bp = Blueprint('games', __name__)

from app.games import routes

