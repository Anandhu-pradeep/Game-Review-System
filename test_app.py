import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

base_url = 'http://localhost:5000'

# Create cookie jar and opener
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def request(url, data=None, headers=None, method=None):
    if headers is None:
        headers = {}
    if data is not None:
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    if method:
        req.get_method = lambda: method
    try:
        with opener.open(req) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, body, resp.headers
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else ""
        return e.code, body, e.headers

def extract_csrf(html_text):
    match = re.search(r'name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', html_text)
    if not match:
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_text)
    return match.group(1) if match else None

print("=== Running GameShelf Integration Tests (Standard Library) ===")

# 1. Public Pages
status, body, _ = request(f'{base_url}/')
assert status == 200 and "GameShelf" in body
print("[PASS] 1. Home page accessible (200 OK)")

status, body, _ = request(f'{base_url}/games')
assert status == 200 and "Game Catalogue" in body
print("[PASS] 2. Games catalogue accessible (200 OK)")

status, body, _ = request(f'{base_url}/games/cyberpunk-2077-phantom-liberty')
assert status == 200 and "Cyberpunk 2077: Phantom Liberty" in body
print("[PASS] 3. Game detail page accessible (200 OK)")

# 2. User Registration
status, body, _ = request(f'{base_url}/register')
csrf = extract_csrf(body)
assert csrf, "CSRF token not found on register page"

import time
unique_user = f"critic_{int(time.time())}"
user_payload = {
    'csrf_token': csrf,
    'username': unique_user,
    'email': f"{unique_user}@gameshelf.com",
    'password': 'SafePassword123!',
    'confirm_password': 'SafePassword123!'
}
status, body, _ = request(f'{base_url}/register', data=user_payload)
assert status == 200 and unique_user in body
print("[PASS] 4. User registration & session establishment successful")

# 3. Rate Game
csrf = extract_csrf(body)
status, body, _ = request(
    f'{base_url}/games/1/rate',
    data={'score': 5, 'csrf_token': csrf},
    headers={'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf}
)
assert status == 200
rate_json = json.loads(body)
assert rate_json['success'] is True
print(f"[PASS] 5. Star rating API: score={rate_json['score']}, new avg={rate_json['average_rating']}")

# 4. Toggle Like
status, body, _ = request(
    f'{base_url}/games/1/like',
    data={'csrf_token': csrf},
    headers={'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf}
)
assert status == 200
like_json = json.loads(body)
assert like_json['success'] is True and like_json['liked'] is True
print(f"[PASS] 6. Game like toggle: liked={like_json['liked']}, count={like_json['likes_count']}")

# 5. Toggle Wishlist
status, body, _ = request(
    f'{base_url}/games/1/wishlist',
    data={'csrf_token': csrf},
    headers={'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf}
)
assert status == 200
wish_json = json.loads(body)
assert wish_json['success'] is True and wish_json['in_wishlist'] is True
print(f"[PASS] 7. Game wishlist toggle: in_wishlist={wish_json['in_wishlist']}")

# 6. Post Review
review_payload = {
    'csrf_token': csrf,
    'title': 'Stunning Masterpiece',
    'content': 'The graphics, characters, and atmosphere are completely breathtaking. A true milestone in open world RPGs.',
    'rating_score': '5'
}
status, body, _ = request(f'{base_url}/games/1/reviews', data=review_payload)
assert status == 200 and 'Stunning Masterpiece' in body
print("[PASS] 8. Review submission & listing verified")

# 7. Check User Dashboard pages
status, body, _ = request(f'{base_url}/profile')
assert status == 200 and unique_user in body
status, body, _ = request(f'{base_url}/my-reviews')
assert status == 200 and 'Stunning Masterpiece' in body
status, body, _ = request(f'{base_url}/my-wishlist')
assert status == 200 and 'Cyberpunk 2077' in body
status, body, _ = request(f'{base_url}/my-ratings')
assert status == 200
print("[PASS] 9. User dashboard pages (Profile, Reviews, Wishlist, Ratings) all verified (200 OK)")

# 8. Admin Authentication & Dashboard
admin_cj = http.cookiejar.CookieJar()
admin_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cj))

def admin_req(url, data=None):
    if data is not None:
        data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    with admin_opener.open(req) as resp:
        return resp.status, resp.read().decode('utf-8')

_, login_body = admin_req(f'{base_url}/login')
admin_csrf = extract_csrf(login_body)
status, admin_body = admin_req(
    f'{base_url}/login',
    data={'csrf_token': admin_csrf, 'login_input': 'admin', 'password': 'Admin123!'}
)
assert status == 200
assert 'Admin Portal' in admin_body or 'Administration Overview' in admin_body
print("[PASS] 10. Admin login & overview dashboard verified (200 OK)")

# 9. Admin Game Management, Users & Stats
status, games_body = admin_req(f'{base_url}/admin/games')
assert status == 200 and 'Manage Game Catalogue' in games_body
status, genres_body = admin_req(f'{base_url}/admin/genres')
assert status == 200 and 'Manage Genres' in genres_body
status, plat_body = admin_req(f'{base_url}/admin/platforms')
assert status == 200 and 'Manage Platforms' in plat_body
status, users_body = admin_req(f'{base_url}/admin/users')
assert status == 200 and unique_user in users_body
status, stats_body = admin_req(f'{base_url}/admin/statistics')
assert status == 200 and 'Platform & Catalog Statistics' in stats_body
print("[PASS] 11. Admin sub-panels (Games, Genres, Platforms, Users, Statistics) all verified (200 OK)")

print("\n🎉 ALL TESTS PASSED! GameShelf is completely verified and operational.")
