import sys
import os
import argparse
from datetime import datetime, date
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User, Genre, Platform, Game, Rating, Review, ReviewComment, Like, Wishlist, slugify
from app.utils.image_generator import generate_gradient_image, generate_avatar_image

app = create_app(os.environ.get('FLASK_ENV', 'development'))

def init_db():
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("Database schema created successfully.")

def create_admin(username=None, email=None, password=None):
    with app.app_context():
        username = username or os.environ.get('ADMIN_USERNAME', 'admin')
        email = email or os.environ.get('ADMIN_EMAIL', 'admin@gameshelf.com')
        password = password or os.environ.get('ADMIN_PASSWORD', 'Admin123!')

        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            user.role = 'admin'
            user.is_active = True
            user.avatar = 'alex.jpg'
            user.set_password(password)
            db.session.commit()
            print(f"Existing user '{user.username}' updated with admin role.")
        else:
            admin = User(
                username=username,
                email=email,
                role='admin',
                bio='Lead Curator and Administrator of GameShelf community platform.',
                avatar='alex.jpg',
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account created successfully: {username} ({email})")

def seed_data():
    with app.app_context():
        db.create_all()
        print("Seeding initial platform data...")

        # 1. Default Avatar
        avatar_path = Path(app.config['AVATARS_FOLDER']) / 'default_avatar.png'
        if not avatar_path.exists():
            generate_avatar_image(200, (40, 48, 70), "GS", avatar_path)
            print("Generated default avatar image.")

        # 2. Seed Admin & Reference Community Users
        create_admin()
        admin_user = User.query.filter_by(role='admin').first()

        community_users_data = [
            ("Alex Ryan", "alex_ryan", "alex@gameshelf.com", "alex.jpg", "Senior game critic and competitive gamer. Level 99 curator."),
            ("Esther Howard", "esther_howard", "esther@gameshelf.com", "esther.jpg", "Strategy enthusiast, retro arcade fan, and community moderator."),
            ("Jacob Jones", "jacob_jones", "jacob@gameshelf.com", "jacob.jpg", "FPS specialist and speedrunner. Loves tactical gameplay."),
            ("Cody Fisher", "cody_fisher", "cody@gameshelf.com", "cody.jpg", "Action-adventure and open-world explorer. 500+ hours logged.")
        ]

        seeded_users = []
        for full_name, u_name, u_email, u_avatar, u_bio in community_users_data:
            existing = User.query.filter_by(username=u_name).first()
            if not existing:
                u = User(
                    username=u_name,
                    email=u_email,
                    role='user',
                    avatar=u_avatar if (Path(app.config['AVATARS_FOLDER']) / u_avatar).exists() else 'default_avatar.png',
                    bio=u_bio,
                    is_active=True
                )
                u.set_password("Gamer123!")
                db.session.add(u)
                db.session.commit()
                seeded_users.append(u)
            else:
                seeded_users.append(existing)

        gamer = seeded_users[0] if seeded_users else admin_user

        # 3. Seed Genres
        genres_data = [
            ("Action", "Fast-paced games focusing on physical challenges and hand-eye coordination."),
            ("RPG", "Role-playing games with character progression, quests, and deep narratives."),
            ("Adventure", "Exploration, puzzle-solving, and narrative-driven storytelling."),
            ("Sci-Fi", "Futuristic themes, high technology, space exploration, and cybernetic worlds."),
            ("Open World", "Vast non-linear virtual worlds with dynamic sandbox gameplay."),
            ("Strategy", "Tactical decision making, base building, and resource management."),
            ("Shooter", "First-person and third-person weapon-based action and combat."),
            ("Battle Royale", "Multiplayer last-player-standing competitive combat."),
            ("Fighting", "Martial arts and combat tournaments."),
            ("Indie", "Unique artistic experiences crafted by passionate independent studios.")
        ]

        genre_map = {}
        for name, desc in genres_data:
            g = Genre.query.filter_by(name=name).first()
            if not g:
                g = Genre(name=name, description=desc)
                db.session.add(g)
                db.session.commit()
            genre_map[name] = g
        print(f"Genres populated ({len(genre_map)} total).")

        # 4. Seed Platforms
        platforms_data = [
            ("PC", "bi-pc-display"),
            ("PlayStation 5", "bi-playstation"),
            ("Xbox Series X/S", "bi-xbox"),
            ("Nintendo Switch", "bi-nintendo-switch"),
            ("PlayStation 4", "bi-playstation")
        ]

        platform_map = {}
        for name, icon in platforms_data:
            p = Platform.query.filter_by(name=name).first()
            if not p:
                p = Platform(name=name, icon_class=icon)
                db.session.add(p)
                db.session.commit()
            platform_map[name] = p
        print(f"Platforms populated ({len(platform_map)} total).")

        # 5. Seed Reference & Showcase Games
        games_to_seed = [
            {
                "title": "Marvel's Spider-Man Remastered",
                "slug": "marvels-spider-man-remastered",
                "description": "Worlds collide in an original action-packed story. Play as Peter Parker battling iconic Marvel villains in Marvel's New York. Web-swing through vibrant neighborhoods and defeat criminals with epic takedowns.",
                "release_date": date(2022, 8, 12),
                "developer": "Insomniac Games",
                "publisher": "PlayStation Publishing",
                "game_mode": "Single-player",
                "genres": ["Action", "Adventure", "Open World"],
                "platforms": ["PC", "PlayStation 5"],
                "cover_file": "spiderman-cover.jpg",
                "banner_file": "spiderman-banner.jpg",
                "top_col": (40, 10, 20),
                "bot_col": (220, 20, 60),
                "accent": "Superhero Action"
            },
            {
                "title": "Apex Legends Season IX",
                "slug": "apex-legends-season-ix",
                "description": "Conquer with character in Apex Legends, a free-to-play hero shooter where legendary characters battle for glory, fame, and fortune on the fringes of the Frontier.",
                "release_date": date(2021, 5, 4),
                "developer": "Respawn Entertainment",
                "publisher": "Electronic Arts",
                "game_mode": "Multiplayer",
                "genres": ["Action", "Shooter", "Battle Royale", "Strategy"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "apex-legends-cover.jpg",
                "banner_file": "apex-legends-cover.jpg",
                "top_col": (20, 15, 40),
                "bot_col": (138, 43, 226),
                "accent": "Battle Royale"
            },
            {
                "title": "Overwatch 2: Strategic Gameplay",
                "slug": "overwatch-2-strategic-gameplay",
                "description": "An always-on and ever-evolving free-to-play, team-based action game set in an optimistic future, where every match is the ultimate 5v5 battlefield brawl.",
                "release_date": date(2022, 10, 4),
                "developer": "Blizzard Entertainment",
                "publisher": "Blizzard Entertainment",
                "game_mode": "Multiplayer",
                "genres": ["Action", "Shooter", "Strategy"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "overwatch-cover.jpg",
                "banner_file": "overwatch-cover.jpg",
                "top_col": (30, 20, 10),
                "bot_col": (255, 120, 0),
                "accent": "Hero Shooter"
            },
            {
                "title": "Ghost of Tsushima",
                "slug": "ghost-of-tsushima",
                "description": "In the late 13th century, the Mongol empire has laid waste to entire nations along their campaign to conquer the East. Tsushima Island is all that stands between mainland Japan and a massive Mongol invasion fleet.",
                "release_date": date(2020, 7, 17),
                "developer": "Sucker Punch Productions",
                "publisher": "Sony Interactive Entertainment",
                "game_mode": "Single-player",
                "genres": ["Action", "Adventure", "Open World"],
                "platforms": ["PC", "PlayStation 5", "PlayStation 4"],
                "cover_file": "ghost-of-tsushima-cover.jpg",
                "banner_file": "ghost-of-tsushima-cover.jpg",
                "top_col": (15, 25, 20),
                "bot_col": (0, 210, 255),
                "accent": "Samurai Action"
            },
            {
                "title": "Street Fighter 6: Clash of Empire",
                "slug": "street-fighter-6-clash-of-empire",
                "description": "Powered by Capcom’s proprietary RE ENGINE, the Street Fighter 6 experience spans across three distinct game modes featuring World Tour, Fighting Ground and Battle Hub.",
                "release_date": date(2023, 6, 2),
                "developer": "Capcom",
                "publisher": "Capcom",
                "game_mode": "Both",
                "genres": ["Action", "Fighting", "Strategy"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "street-fighter-cover.jpg",
                "banner_file": "street-fighter-cover.jpg",
                "top_col": (25, 10, 30),
                "bot_col": (217, 70, 239),
                "accent": "Fighting"
            },
            {
                "title": "Cyberpunk 2077: Phantom Liberty",
                "slug": "cyberpunk-2077-phantom-liberty",
                "description": "Step into the neon-drenched streets of Night City and the dangerous new district of Dogtown. Phantom Liberty is an espionage-thriller adventure for Cyberpunk 2077, bringing refined mechanics, intense cyberware combat, and an unforgettable story starring Keanu Reeves and Idris Elba.",
                "release_date": date(2023, 9, 26),
                "developer": "CD PROJEKT RED",
                "publisher": "CD PROJEKT RED",
                "game_mode": "Single-player",
                "genres": ["RPG", "Sci-Fi", "Open World", "Shooter"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "cyberpunk-cover.jpg",
                "banner_file": "cyberpunk-banner.jpg",
                "top_col": (20, 10, 40),
                "bot_col": (255, 42, 95),
                "accent": "Cyber RPG"
            },
            {
                "title": "Elden Ring: Shadow of the Erdtree",
                "slug": "elden-ring-shadow-of-the-erdtree",
                "description": "Guided by Empyrean Miquella, players are summoned to the Land of Shadow, a place obscured by the Erdtree where the goddess Marika first set foot. Unravel dark secrets, explore treacherous dungeons, and face colossal new bosses in FromSoftware's critically acclaimed masterpiece.",
                "release_date": date(2024, 6, 21),
                "developer": "FromSoftware Inc.",
                "publisher": "Bandai Namco Entertainment",
                "game_mode": "Both",
                "genres": ["Action", "RPG", "Open World"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S", "PlayStation 4"],
                "cover_file": "elden-ring-cover.jpg",
                "banner_file": "elden-ring-banner.jpg",
                "top_col": (15, 20, 30),
                "bot_col": (212, 175, 55),
                "accent": "Souls Action"
            },
            {
                "title": "Marvel Rivals Gameplay",
                "slug": "marvel-rivals-gameplay",
                "description": "Marvel Rivals is a thrilling 6v6 Super Hero team-based PVP shooter! Assemble an all-star Marvel squad, devise countless strategies by combining powers to form unique Team-Up skills and fight in destructible, ever-changing battlefields.",
                "release_date": date(2024, 12, 6),
                "developer": "NetEase Games",
                "publisher": "NetEase Games",
                "game_mode": "Multiplayer",
                "genres": ["Action", "Shooter", "Strategy"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "marvel-rivals-cover.jpg",
                "banner_file": "marvel-rivals-cover.jpg",
                "top_col": (35, 10, 45),
                "bot_col": (217, 70, 239),
                "accent": "Super Hero Shooter"
            },
            {
                "title": "Clash of Clan Emulator",
                "slug": "clash-of-clan-emulator",
                "description": "Build your village, raise a clan, and compete in epic Clan Wars! Join millions of players worldwide as you build your base, customize defenses, and clash against rival clans in strategic warfare.",
                "release_date": date(2023, 1, 15),
                "developer": "Supercell",
                "publisher": "Supercell",
                "game_mode": "Multiplayer",
                "genres": ["Strategy", "Battle Royale"],
                "platforms": ["PC"],
                "cover_file": "clash-cover.jpg",
                "banner_file": "clash-cover.jpg",
                "top_col": (30, 20, 10),
                "bot_col": (234, 179, 8),
                "accent": "Base Building Strategy"
            },
            {
                "title": "NFS Hot Persuit",
                "slug": "nfs-hot-persuit",
                "description": "Feel the thrill of the chase and the rush of escape in Need for Speed Hot Pursuit. Unleash a savage sense of speed both as an outlaw and a cop in the world's hottest high-performance cars.",
                "release_date": date(2020, 11, 6),
                "developer": "Stellar Entertainment",
                "publisher": "Electronic Arts",
                "game_mode": "Both",
                "genres": ["Action", "Strategy"],
                "platforms": ["PC", "PlayStation 5", "Xbox Series X/S"],
                "cover_file": "nfs-cover.jpg",
                "banner_file": "nfs-cover.jpg",
                "top_col": (40, 15, 10),
                "bot_col": (244, 63, 94),
                "accent": "High Speed Racing"
            }
        ]

        for item in games_to_seed:
            existing_game = Game.query.filter_by(slug=item["slug"]).first()
            
            # Use downloaded high-res file if exists, else fallback
            cover_filename = item.get("cover_file") or f"{item['slug']}-cover.jpg"
            banner_filename = item.get("banner_file") or f"{item['slug']}-banner.jpg"

            cover_dest = Path(app.config['COVERS_FOLDER']) / cover_filename
            banner_dest = Path(app.config['BANNERS_FOLDER']) / banner_filename

            if not cover_dest.exists():
                generate_gradient_image(600, 900, item["top_col"], item["bot_col"], item["title"][:22], item["accent"], cover_dest)
            if not banner_dest.exists():
                generate_gradient_image(1280, 500, item["top_col"], item["bot_col"], item["title"], item["developer"], banner_dest)

            if not existing_game:
                g = Game(
                    title=item["title"],
                    slug=item["slug"],
                    description=item["description"],
                    release_date=item["release_date"],
                    developer=item["developer"],
                    publisher=item["publisher"],
                    game_mode=item["game_mode"],
                    cover_image=cover_filename,
                    banner_image=banner_filename
                )
                g.genres = [genre_map[name] for name in item["genres"] if name in genre_map]
                g.platforms = [platform_map[name] for name in item["platforms"] if name in platform_map]
                db.session.add(g)
                db.session.commit()
                print(f"Added showcase game: {g.title}")

                # Add sample ratings
                r1 = Rating(user_id=admin_user.id, game_id=g.id, score=5)
                r2 = Rating(user_id=gamer.id, game_id=g.id, score=5 if "Spider" in g.title else 4)
                db.session.add_all([r1, r2])
                db.session.commit()
                g.recalculate_rating()

                # Add sample community review
                rev = Review(
                    user_id=gamer.id,
                    game_id=g.id,
                    title="Absolute perfection in gaming!",
                    content=f"Simply exceptional game design. The mechanics, visuals, and responsiveness make this an unmatched experience. Highly recommended!",
                    rating_score=5
                )
                db.session.add(rev)
                db.session.commit()

                # Add review comment
                comment = ReviewComment(
                    review_id=rev.id,
                    user_id=admin_user.id,
                    content="100% agreed! Outstanding performance and visuals."
                )
                db.session.add(comment)

                # Add like & wishlist
                db.session.add(Like(user_id=gamer.id, game_id=g.id))
                db.session.add(Wishlist(user_id=admin_user.id, game_id=g.id))
                db.session.commit()
            else:
                # Update images to high-res if needed
                existing_game.cover_image = cover_filename
                existing_game.banner_image = banner_filename
                db.session.commit()

        print("Seeding completed successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="GameShelf CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init-db", help="Initialize all database tables")
    admin_parser = subparsers.add_parser("create-admin", help="Create or elevate an admin account")
    admin_parser.add_argument("--username", help="Admin username")
    admin_parser.add_argument("--email", help="Admin email")
    admin_parser.add_argument("--password", help="Admin password")
    subparsers.add_parser("seed-data", help="Seed initial genres, platforms, and showcase games")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "create-admin":
        create_admin(args.username, args.email, args.password)
    elif args.command == "seed-data":
        seed_data()
    else:
        parser.print_help()
