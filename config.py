# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
ADMIN_CONTACT = "@WatashiWaSenseiBot"

# Plans configuration
PLANS = {
    "free": {"checks_per_day": 25, "priority": 4, "price": 0},
    "weekly": {"checks_per_day": 50, "priority": 3, "price": 5},
    "monthly": {"checks_per_day": float("inf"), "priority": 2, "price": 10},
    "yearly": {"checks_per_day": float("inf"), "priority": 1, "price": 50},
    "admin": {"checks_per_day": float("inf"), "priority": 0, "price": 0},
}

# Services list with URLs and selectors
SERVICES = {
    "netflix": {"name": "Netflix", "icon": "🎬", "login_url": "https://www.netflix.com/login"},
    "disney": {"name": "Disney+", "icon": "🐭", "login_url": "https://www.disneyplus.com/login"},
    "hbomax": {"name": "HBO Max", "icon": "🎞️", "login_url": "https://www.max.com/login"},
    "prime": {"name": "Prime Video", "icon": "📦", "login_url": "https://www.amazon.com/ap/signin"},
    "hulu": {"name": "Hulu", "icon": "📺", "login_url": "https://www.hulu.com/login"},
    "crunchyroll": {"name": "Crunchyroll", "icon": "🍣", "login_url": "https://www.crunchyroll.com/login"},
    "paramount": {"name": "Paramount+", "icon": "🎯", "login_url": "https://www.paramountplus.com/login/"},
    "peacock": {"name": "Peacock", "icon": "🦚", "login_url": "https://www.peacocktv.com/signin"},
    "plex": {"name": "Plex", "icon": "🎬", "login_url": "https://app.plex.tv/auth/#!"},
    "starz": {"name": "Starz", "icon": "⭐", "login_url": "https://www.starz.com/login"},
    "mgm": {"name": "MGM+", "icon": "🎪", "login_url": "https://www.mgmplus.com/login"},
    "discovery": {"name": "Discovery+", "icon": "📡", "login_url": "https://www.discoveryplus.com/login"},
    "espn": {"name": "ESPN+", "icon": "⚽", "login_url": "https://www.espn.com/login"},
    "tubi": {"name": "Tubi", "icon": "🟢", "login_url": "https://tubitv.com/signin"},
    "pluto": {"name": "Pluto TV", "icon": "📡", "login_url": "https://pluto.tv/login"},
    "spotify": {"name": "Spotify", "icon": "🎵", "login_url": "https://accounts.spotify.com/en/login"},
    "youtube_music": {"name": "YouTube Music", "icon": "🎧", "login_url": "https://music.youtube.com/"},
    "amazon_music": {"name": "Amazon Music", "icon": "🎵", "login_url": "https://www.amazon.com/music/player"},
    "chatgpt": {"name": "ChatGPT", "icon": "🤖", "login_url": "https://chat.openai.com/auth/login"},
    "claude": {"name": "Claude AI", "icon": "🧠", "login_url": "https://claude.ai/login"},
    "perplexity": {"name": "Perplexity", "icon": "🔍", "login_url": "https://www.perplexity.ai/login"},
    "cursor": {"name": "Cursor", "icon": "⚡", "login_url": "https://cursor.sh/login"},
    "surfshark": {"name": "Surfshark", "icon": "🦈", "login_url": "https://account.surfshark.com/login"},
    "nordvpn": {"name": "NordVPN", "icon": "🛡️", "login_url": "https://my.nordaccount.com/login/"},
    "expressvpn": {"name": "ExpressVPN", "icon": "🔒", "login_url": "https://www.expressvpn.com/login"},
    "canva": {"name": "Canva Pro", "icon": "🎨", "login_url": "https://www.canva.com/login"}
}

# Checker settings
TIMEOUT_DEFAULT = 120  # <--- CHANGED FROM 15/45/90 TO 120
MAX_CONCURRENT = 2  # Reduced from 3 to avoid overload
MAX_RETRIES = 2
