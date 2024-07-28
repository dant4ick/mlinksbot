import time
import aiohttp
from urllib.parse import quote_plus
from config import CLIENT_ID, CLIENT_SECRET

class SpotifyTokenManager:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = None

    async def get_token(self) -> str:
        if self.token is None or time.time() > self.token_expiry:
            await self.fetch_new_token()
        return self.token

    async def fetch_new_token(self):
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                response_data = await response.json()
                self.token = response_data["access_token"]
                self.token_expiry = time.time() + 3590  # 1 hour minus 10 seconds

SPOTIFY_TOKEN_MANAGER = SpotifyTokenManager(CLIENT_ID, CLIENT_SECRET)

async def search_spotify(query, types='track', market=None, limit=1, offset=0, include_external=None):
    url = "https://api.spotify.com/v1/search?"
    
    params = {
        'q': query,
        'type': types,
        'market': market,
        'limit': limit,
        'offset': offset,
        'include_external': include_external
    }
    
    url += "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items() if v])
    
    SPOTIFY_TOKEN = await SPOTIFY_TOKEN_MANAGER.get_token()
    
    headers = {'Authorization': f'Bearer {SPOTIFY_TOKEN}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                json_response = await response.json()
                return [
                    {
                        'artist': track['artists'][0]['name'],
                        'title': track['name'],
                        'url': track['external_urls']['spotify'],
                        'id': track['id']
                    }
                    for track in json_response['tracks']['items']
                ]
            else:
                logging.error(f"Failed to search Spotify: {response.status}")
                logging.error(await response.text())
                return []


async def fetch_song_info(url: str):
    api_url = f"https://api.song.link/v1-alpha.1/links?url={url}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                return process_song_info(data)

def process_song_info(data: dict):
    song_data = data.get('entitiesByUniqueId', {})
    result = {}

    for key, value in song_data.items():
        if 'thumbnailUrl' in value and "ANGHAMI_SONG" not in key and "BOOMPLAY_SONG" not in key and "YOUTUBE" not in key and "SOUNDCLOUD" not in key:
            result = {
                'platform_urls': {'All': data.get('pageUrl')},
                'title': value.get('title'),
                'artistName': value.get('artistName'),
                'thumbnailUrl': value.get('thumbnailUrl')
            }
            break

    if result and 'linksByPlatform' in data:
        platforms = {'spotify': 'Spotify', 'yandex': 'Yandex', 'youtubeMusic': 'YTMusic'}
        platforms_data = data['linksByPlatform']

        for platform, platform_name in platforms.items():
            if platform in platforms_data:
                result['platform_urls'][platform_name] = platforms_data[platform]['url']

    return result
