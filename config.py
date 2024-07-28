import os
from pathlib import Path

API_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

URL_PATTERN = r'[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'downloads' / 'downloads.db'
COOKIE_FILE = BASE_DIR / 'downloads' / 'youtube_cookies.txt'
CACHE_DIR = BASE_DIR / 'downloads' / 'cache'
