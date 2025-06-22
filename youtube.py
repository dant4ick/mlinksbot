import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import aiofiles
from spotify import fetch_song_info
import yt_dlp as youtube_dl
from config import COOKIE_FILE, CACHE_DIR, YOUTUBE_USERNAME, YOUTUBE_PASSWORD
from aiogram import types
from shared import bot
from utils import create_message_text
from database import get_file_id, save_file_id

executor = ThreadPoolExecutor(max_workers=4)

# Proxy configuration for yt-dlp
PROXY_URL = "socks5://127.0.0.1:1080"

def download_audio(url: str):
    ydl_opts = {
        'cookiefile': COOKIE_FILE,
        'proxy': PROXY_URL,
        
        # 'verbose': True,
        'quiet': True,
        
        'outtmpl': f'{CACHE_DIR}/%(id)s.%(ext)s',
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        track_duration = info_dict.get('duration', 0)

        if track_duration > 10 * 60:
            return 'Track is too long'

        ydl.download([url])

        temp_filename = ydl.prepare_filename(info_dict)
        filename = f"{os.path.splitext(temp_filename)[0]}.mp3"

        return (
            filename,
            track_duration,
            info_dict.get('uploader', ''),
            info_dict.get('title', ''),
            info_dict.get('thumbnail', '')
        )

async def download_and_send_audio(res: types.ChosenInlineResult):
    url = res.result_id
    file_id = await get_file_id(url)

    if not file_id:
        try:
            audio_file = await asyncio.get_event_loop().run_in_executor(executor, lambda: download_audio(url))
        except Exception as e:
            await report_download_failure(res, str(e))
            return

        if not audio_file:
            await report_download_failure(res)
            return
        elif audio_file == 'Track is too long':
            await report_download_failure(res, 'Track is too long')
            return

        filename, duration, performer, title, thumbnail = audio_file
        async with aiofiles.open(filename, 'rb') as f:
            input_file = types.FSInputFile(f.name)
            file_msg = await bot.send_audio(res.from_user.id, input_file, duration=duration, performer=performer, title=title, thumbnail=types.URLInputFile(thumbnail))
        file_id = file_msg.audio.file_id

        await save_file_id(url, file_id)
        os.remove(filename)

    song_info = await fetch_song_info(url)
    caption = await create_message_text(song_info)
    await bot.edit_message_media(inline_message_id=res.inline_message_id, media=types.InputMediaAudio(media=file_id, caption=caption))


async def report_download_failure(res, e: str = None):
    await bot.send_message(res.from_user.id, f"Failed to download the track. \n\n<code>{e or ''}</code>")
    await bot.edit_message_reply_markup(
        inline_message_id=res.inline_message_id,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Error", callback_data="download_error")]
        ])
    )
