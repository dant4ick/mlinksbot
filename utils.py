import os
from html import escape
from aiogram import types
from shared import bot

async def create_message_text(song_info: dict) -> str:
    bot_info = await bot.get_me()
    song_urls = " | ".join([f"<a href='{escape(song_url)}'>{escape(song_name)}</a>" for song_name, song_url in song_info['platform_urls'].items()])
    
    # Check if it's an album
    is_album = song_info.get('type') == 'album'
    emoji = "💿" if is_album else "🎸"
    content_type = "Album" if is_album else "Track"
    
    msg_text = f"<code>{escape(song_info['artistName'])} - {escape(song_info['title'])}</code>\n\n{emoji} {content_type}: {song_urls} {emoji}\n\n@{bot_info.username}"
    return msg_text


async def generate_inline_query_results(song_info: dict, preview=False) -> list:
    message_text = await create_message_text(song_info)
    yt_url = song_info['platform_urls'].get('YTMusic')
    is_album = song_info.get('type') == 'album'

    result = []
    
    input_content = types.InputTextMessageContent(
        message_text=message_text,
        link_preview_options=types.LinkPreviewOptions(url=song_info['thumbnailUrl'], prefer_large_media=True, show_above_text=True)
    )
    result.append(types.InlineQueryResultArticle(
        id=song_info['platform_urls'].get('All'),
        title=song_info['title'],
        description=f"by {song_info['artistName']}",
        thumbnail_url=song_info['thumbnailUrl'],
        input_message_content=input_content
    ))
    
    # Only add download option for songs, not albums
    if yt_url and not preview and not is_album:
        result.append(types.InlineQueryResultAudio(
            id=yt_url,
            title=song_info['title'],
            performer=song_info['artistName'],
            audio_url=os.environ.get('LOADING_AUDIO_ID'),
            caption=message_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Downloading...", callback_data=yt_url)]
            ])
    ))
    
    return result
