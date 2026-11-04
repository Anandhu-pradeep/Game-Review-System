# GameShelf – Gaming Community & Review Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg)](https://getbootstrap.com)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com)

**GameShelf** is a modern, responsive, and complete gaming community web application where gamers discover video games, rate games on a 1-to-5 star scale, post in-depth reviews, comment on reviews, like games, track wishlists, and manage their gaming profiles.

---

## Features

### 🎮 Game Discovery & Catalogue
- **Global Search & Multi-Filter Engine**: Search games by title, developer, or publisher. Filter games across multiple genres (Action, RPG, Sci-Fi, Souls-like, etc.) and hardware platforms (PC, PS5, Xbox Series X/S, Nintendo Switch, etc.).
- **Smart Sorting**: Sort by highest rated, most popular, newest release, or alphabetical.
- **Detailed Game Pages**: High-resolution box art, landscape banner artwork, developer & publisher credentials, release dates, and game mode indicators (Single-player, Multiplayer, Both).
- **Automated Rating Calculations**: Dynamic real-time calculation of average user rating and total ratings count.

### 🌟 Community Rating & Review System
- **1-5 Star Community Ratings**: Interactive 5-star rating widget with instant AJAX persistence and automatic average updates.
- **In-Depth Reviews**: User critiques with optional headlines, star scores, and markdown/text content.
- **Nested Review Comments**: Community replies and discussions directly beneath member reviews.
- **Sorting for Reviews**: Sort reviews by newest, oldest, or highest rated.
- **Owner & Admin Controls**: Edit or delete reviews with modal dialogs and safety confirmation checks.

### 👥 Social Features
- **Like / Unlike Games**: Instant bookmarking of favorite games with live counters.
- **Gaming Wishlist**: Save backlogged games to personal wishlist with 1-click removal.
- **In-App Notification Center**: Instant alerts when community members reply to or interact with your reviews.
- **Activity Stream Timeline**: Chronological history of user actions (rated, reviewed, liked, wishlisted).
- **Public & Private Profiles**: Customizable gamer bio, avatar upload, and showcase of reviews, ratings, and wishlists.

### 🛡️ Role-Based Administration
- **Dedicated Admin Portal**: Separate dark gaming layout with navigation sidebar.
- **Game Management**: Add new titles, update game information, and upload cover and banner artwork.
- **Genre & Platform Management**: Create, edit, and curate genres and platforms.
- **User Moderation**: View all registered users, activate or deactivate accounts, and promote/demote administrator privileges.
- **Content Moderation**: Review and delete inappropriate reviews and replies.
- **Statistics & Analytics**: Distribution of games by genre and platform, top rated games, most reviewed titles, and engagement totals.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Dark Gaming Theme), Bootstrap 5, Bootstrap Icons, JavaScript (Fetch API) |
| **Backend** | Python 3.11, Flask 3.0.3 |
| **Database** | PostgreSQL 16 |
| **ORM & Migrations** | Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.0.7 |
| **Authentication** | Flask Sessions with Werkzeug password hashing |
| **Image Handling** | Pillow (PIL) image verification, resizing, and persistent storage |
| **Containerization** | Docker, Docker Compose |
| **Web Server** | Gunicorn (3 workers, 2 threads) |

---

## Project Structure

```
GameShelf/
├── app/
│   ├── __init__.py           # Application factory, CSRF filter, template filters
│   ├── extensions.py         # SQLAlchemy and Migrate instances
│   ├── models.py             # Relational PostgreSQL models & constraints
│   ├── auth/                 # Authentication blueprint (login, register, logout)
│   ├── admin/                # Admin portal blueprint & moderation routes
│   ├── games/                # Game catalogue, detail, rate, like, wishlist routes
│   ├── reviews/              # Community reviews and replies routes
│   ├── users/                # Dashboard, public profiles, settings, notifications
│   ├── utils/
│   │   ├── decorators.py     # @login_required, @admin_required
│   │   ├── helpers.py        # Image upload handling, activity logger, notifications
│   │   ├── security.py       # CSRF token generation and validation
│   │   └── image_generator.py# Default avatars and placeholder generation
│   ├── templates/            # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/
│   │   ├── games/
│   │   ├── users/
│   │   ├── admin/
│   │   └── errors/
│   └── static/
│       ├── css/style.css     # Premium dark gaming styling
│       ├── js/main.js        # Star ratings, like/wishlist AJAX, modals
│       └── uploads/          # Persistent storage (covers, banners, avatars)
├── Dockerfile                # Multi-stage lightweight Python container
├── docker-compose.yml        # Orchestration with PostgreSQL 16 & healthchecks
├── entrypoint.sh             # DB wait check, auto migrations, seeding & Gunicorn start
├── cli.py                    # Flask CLI for init-db, create-admin, seed-data
├── config.py                 # Environment configuration classes
├── requirements.txt          # Python dependencies
├── .env.example              # Sample environment variables
├── .dockerignore
└── README.md
```

---

## Ubuntu Terminal Installation & Run Guide

### 1. Prerequisites (Ubuntu 20.04 / 22.04 / 24.04 LTS)

Update package index and install Docker and Docker Compose:

```bash
# Update Ubuntu packages
sudo apt update && sudo apt upgrade -y

# Install Docker engine and Docker Compose plugin
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify Docker installation
docker --version
docker compose version
```

---

### 2. Configure Environment

Clone or navigate to the project directory:

```bash
cd GameShelf

# Copy environment variables file
cp .env.example .env
```

You can customize `.env` if desired (database credentials, admin email, secret key).

---

### 3. Build & Start with Docker Compose

Launch the PostgreSQL database and Flask web container:

```bash
docker compose up --build -d
```

The startup script (`entrypoint.sh`):
1. Waits for PostgreSQL to become fully healthy (`pg_isready`).
2. Creates all relational database tables.
3. Automatically seeds initial genres, platforms, default admin account, and showcase games.
4. Spawns Gunicorn on port `5000`.

---

### 4. Access the Application

Open your browser and navigate to:

👉 **[http://localhost:5000](http://localhost:5000)**

---

### 5. Default Accounts

| Role | Username / Email | Password | Access |
|---|---|---|---|
| **Administrator** | `admin` / `admin@gameshelf.com` | `Admin123!` | [http://localhost:5000/admin](http://localhost:5000/admin) |
| **Community Gamer** | `pixel_warrior` / `gamer@gameshelf.com` | `Gamer123!` | Public site & User Dashboard |

---

### 6. CLI Management Commands

You can run administrative commands directly within the running Docker web container:

#### Create or Elevate an Admin Account:
```bash
docker compose exec web python cli.py create-admin --username myadmin --email myadmin@gameshelf.com --password "MySecretPass123!"
```

#### Re-seed Showcase Data:
```bash
docker compose exec web python cli.py seed-data
```

#### Initialize Database Schema:
```bash
docker compose exec web python cli.py init-db
```

---

### 7. Stopping and Restarting the Application

```bash
# View running container status
docker compose ps

# View real-time container logs
docker compose logs -f web

# Stop containers without losing data (volumes remain intact)
docker compose down

# Restart containers
docker compose up -d
```

---

### 8. Troubleshooting Common Errors

#### Issue 1: Port 5000 or 5432 is already in use
```bash
# Check what is using port 5000 or 5432
sudo lsof -i :5000
sudo lsof -i :5432

# Or modify the port mappings in docker-compose.yml:
# ports:
#   - "5001:5000"
```

#### Issue 2: Permission denied when uploading images
Ensure the persistent uploads directory within the container has write permissions:
```bash
docker compose exec web mkdir -p /app/app/static/uploads/covers /app/app/static/uploads/banners /app/app/static/uploads/avatars
```

#### Issue 3: Resetting database completely
```bash
# Stop containers and destroy persistent database volume
docker compose down -v

# Re-launch and re-seed from scratch
docker compose up --build -d
```

