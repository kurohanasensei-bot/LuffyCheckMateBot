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
    "netflix": {
        "name": "Netflix",
        "icon": "🎬",
        "login_url": "https://www.netflix.com/login",
        "account_url": "https://www.netflix.com/AccountDetails"
    },
    "disney": {
        "name": "Disney+",
        "icon": "🐭",
        "login_url": "https://www.disneyplus.com/login",
        "account_url": "https://www.disneyplus.com/account"
    },
    "hbomax": {
        "name": "HBO Max",
        "icon": "🎞️",
        "login_url": "https://www.max.com/login",
        "account_url": "https://www.max.com/account"
    },
    "prime": {
        "name": "Prime Video",
        "icon": "📦",
        "login_url": "https://www.primevideo.com/auth/ref=nav_ham_signin",
        "account_url": "https://www.amazon.com/gp/css/account/view.html"
    },
    "hulu": {
        "name": "Hulu",
        "icon": "📺",
        "login_url": "https://www.hulu.com/login",
        "account_url": "https://www.hulu.com/account"
    },
    "crunchyroll": {
        "name": "Crunchyroll",
        "icon": "🍣",
        "login_url": "https://www.crunchyroll.com/login",
        "account_url": "https://www.crunchyroll.com/premium"
    },
    "paramount": {
        "name": "Paramount+",
        "icon": "🎯",
        "login_url": "https://www.paramountplus.com/login/",
        "account_url": "https://www.paramountplus.com/account/"
    },
    "peacock": {
        "name": "Peacock",
        "icon": "🦚",
        "login_url": "https://www.peacocktv.com/signin",
        "account_url": "https://www.peacocktv.com/account"
    },
    "plex": {
        "name": "Plex",
        "icon": "🎬",
        "login_url": "https://app.plex.tv/auth/#!",
        "account_url": "https://app.plex.tv/desktop/#!/settings/account"
    },
    "starz": {
        "name": "Starz",
        "icon": "⭐",
        "login_url": "https://www.starz.com/login",
        "account_url": "https://www.starz.com/account"
    },
    "mgm": {
        "name": "MGM+",
        "icon": "🎪",
        "login_url": "https://www.mgmplus.com/login",
        "account_url": "https://www.mgmplus.com/account"
    },
    "discovery": {
        "name": "Discovery+",
        "icon": "📡",
        "login_url": "https://www.discoveryplus.com/login",
        "account_url": "https://www.discoveryplus.com/account"
    },
    "espn": {
        "name": "ESPN+",
        "icon": "⚽",
        "login_url": "https://www.espn.com/login",
        "account_url": "https://www.espn.com/plus/account"
    },
    "tubi": {
        "name": "Tubi",
        "icon": "🟢",
        "login_url": "https://tubitv.com/signin",
        "account_url": "https://tubitv.com/account"
    },
    "pluto": {
        "name": "Pluto TV",
        "icon": "📡",
        "login_url": "https://pluto.tv/login",
        "account_url": "https://pluto.tv/account"
    },
    "spotify": {
        "name": "Spotify",
        "icon": "🎵",
        "login_url": "https://accounts.spotify.com/en/login",
        "account_url": "https://www.spotify.com/account/overview/"
    },
    "youtube_music": {
        "name": "YouTube Music",
        "icon": "🎧",
        "login_url": "https://music.youtube.com/",
        "account_url": "https://www.youtube.com/paid_memberships"
    },
    "amazon_music": {
        "name": "Amazon Music",
        "icon": "🎵",
        "login_url": "https://www.amazon.com/music/player",
        "account_url": "https://www.amazon.com/gp/yourmemberships"
    },
    "chatgpt": {
        "name": "ChatGPT",
        "icon": "🤖",
        "login_url": "https://chat.openai.com/auth/login",
        "account_url": "https://chat.openai.com/account"
    },
    "claude": {
        "name": "Claude AI",
        "icon": "🧠",
        "login_url": "https://claude.ai/login",
        "account_url": "https://claude.ai/account"
    },
    "perplexity": {
        "name": "Perplexity",
        "icon": "🔍",
        "login_url": "https://www.perplexity.ai/login",
        "account_url": "https://www.perplexity.ai/account"
    },
    "cursor": {
        "name": "Cursor",
        "icon": "⚡",
        "login_url": "https://cursor.sh/login",
        "account_url": "https://cursor.sh/account"
    },
    "surfshark": {
        "name": "Surfshark",
        "icon": "🦈",
        "login_url": "https://account.surfshark.com/login",
        "account_url": "https://account.surfshark.com/subscription"
    },
    "nordvpn": {
        "name": "NordVPN",
        "icon": "🛡️",
        "login_url": "https://my.nordaccount.com/login/",
        "account_url": "https://my.nordaccount.com/account/dashboard/"
    },
    "expressvpn": {
        "name": "ExpressVPN",
        "icon": "🔒",
        "login_url": "https://www.expressvpn.com/login",
        "account_url": "https://www.expressvpn.com/account"
    },
    "canva": {
        "name": "Canva Pro",
        "icon": "🎨",
        "login_url": "https://www.canva.com/login",
        "account_url": "https://www.canva.com/account"
    }
}

# Checker settings
TIMEOUT_DEFAULT = 15
MAX_CONCURRENT = 3
MAX_RETRIES = 2