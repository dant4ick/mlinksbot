import os
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiohttp_socks import ProxyConnector
from config import API_TOKEN

PROXY_URL = os.environ.get("PROXY_URL", "socks5://shadowsocks:1080")

session = AiohttpSession(connector=ProxyConnector.from_url(PROXY_URL))
bot = Bot(token=API_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
