import asyncio
import logging
import re
import sys
from aiogram import Dispatcher, F, filters, types
from aiogram.enums import ParseMode, ChatAction
from aiogram.methods.delete_webhook import DeleteWebhook
from config import URL_PATTERN, ADMIN_USER_IDS
from spotify import search_spotify, fetch_song_info
from youtube import download_and_send_audio, download_and_send_audio_direct
from utils import generate_inline_query_results, create_message_text
from database import log_action, get_bot_statistics
from shared import bot

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def init_bot():
    dp = Dispatcher()

    @dp.inline_query(F.query.regexp(URL_PATTERN))
    async def search_song(inline_query: types.InlineQuery):
        query = inline_query.query
        
        # Log the inline query action
        await log_action(
            user_id=inline_query.from_user.id,
            username=inline_query.from_user.username,
            action_type="inline_query",
            url=query
        )
        
        song_info = await fetch_song_info(query)

        if song_info:
            result = await generate_inline_query_results(song_info)
            await inline_query.answer(result)
        else:
            await inline_query.answer([
                types.InlineQueryResultArticle(
                    id="1",
                    title="Can't find music links...",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"Tried to share music link: {query}",
                        disable_web_page_preview=True
                    )
                )
            ])

    @dp.inline_query()
    async def default_handler(inline_query: types.InlineQuery):
        query_text = inline_query.query
        if not query_text:
            bot_info = await bot.get_me()
            result = types.InlineQueryResultArticle(
                id="0",
                title='Paste song url or search query in the message field...',
                input_message_content=types.InputTextMessageContent(message_text=f'@{bot_info.username} - share music via any links')
            )
            await inline_query.answer([result])
            return
        
        # Log the inline search query action
        await log_action(
            user_id=inline_query.from_user.id,
            username=inline_query.from_user.username,
            action_type="inline_query",
            query=query_text
        )
        
        search_results = await search_spotify(query_text)
        results = []
        for song in search_results:
            song_info = await fetch_song_info(song['url'])
            result = await generate_inline_query_results(song_info, preview=False)
            results.extend(result)

        await inline_query.answer(results, cache_time=1)

    @dp.message(filters.CommandStart())
    async def start(msg: types.Message):
        bot_info = await bot.get_me()
        tutorial_message = (
            f"👋 Hello! Here's how to use me:\n\n"
            f"🔗 **Send a music link directly:**\n"
            f"Just paste any music URL (Spotify, YouTube, etc.) and I'll download it for you!\n\n"
            f"🔍 **Search for music:**\n"
            f"Type the name of a song or artist and I'll find it for you!\n\n"
            f"⚡ **Use inline mode:**\n"
            f"1️⃣ Type `@{bot_info.username}` in any chat, followed by a space.\n"
            f"2️⃣ Paste the URL or search query.\n"
            f"3️⃣ Choose from the results to share with others.\n\n"
            f"🚀 Try sending me a song now!"
        )
        await msg.answer(tutorial_message, parse_mode=ParseMode.MARKDOWN)
        
        # Log the start command usage
        await log_action(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            action_type="start_command"
        )

    @dp.message(filters.Command("stats"))
    async def show_stats(msg: types.Message):
        """Show bot usage statistics"""
        # Check if user is admin
        if not ADMIN_USER_IDS or msg.from_user.id not in ADMIN_USER_IDS:
            await msg.answer("🚫 This command is only available for bot administrators.")
            return
        
        await bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
        
        try:
            stats = await get_bot_statistics()
            
            # Format statistics message
            stats_text = "📊 **Bot Usage Statistics**\n\n"
            
            # Basic stats
            stats_text += f"👥 **Total Users:** {stats['total_users']}\n"
            stats_text += f"🎯 **Total Actions:** {stats['total_actions']}\n"
            stats_text += f"💾 **Total Downloads:** {stats['total_downloads']}\n\n"
            
            # Actions by type
            if stats['actions_by_type']:
                stats_text += "📈 **Actions by Type:**\n"
                for action_type, count in stats['actions_by_type']:
                    action_emoji = {
                        'start_command': '🚀',
                        'url_download': '🔗',
                        'search_query': '🔍',
                        'inline_query': '⚡'
                    }.get(action_type, '📝')
                    stats_text += f"{action_emoji} {action_type.replace('_', ' ').title()}: {count}\n"
                stats_text += "\n"
            
            # Top users
            if stats['top_users']:
                stats_text += "🏆 **Top Active Users:**\n"
                for i, (username, user_id, action_count) in enumerate(stats['top_users'][:5], 1):
                    user_display = f"@{username}" if username else f"User {user_id}"
                    stats_text += f"{i}. {user_display}: {action_count} actions\n"
                stats_text += "\n"
            
            # Daily stats
            if stats['daily_stats']:
                stats_text += "📅 **Daily Activity (Last 7 Days):**\n"
                for date, count in stats['daily_stats']:
                    stats_text += f"📊 {date}: {count} actions\n"
            
            await msg.answer(stats_text, parse_mode=ParseMode.MARKDOWN)
            
            # Log the stats command usage
            await log_action(
                user_id=msg.from_user.id,
                username=msg.from_user.username,
                action_type="stats_command"
            )
            
        except Exception as e:
            logging.error(f"Error generating statistics: {e}")
            await msg.answer("❌ Error generating statistics. Please try again later.")

    @dp.message(filters.Command("help"))
    async def show_help(msg: types.Message):
        """Show available commands"""
        help_text = (
            "🤖 **Available Commands:**\n\n"
            "🚀 `/start` - Get started with the bot\n"
            "❓ `/help` - Show this help message\n"
        )
        
        # Add stats command for admins
        if ADMIN_USER_IDS and msg.from_user.id in ADMIN_USER_IDS:
            help_text += "📊 `/stats` - View bot usage statistics (Admin only)\n"
        
        help_text += (
            "\n🎵 **How to use:**\n"
            "• Send a music URL (Spotify, YouTube, etc.)\n"
            "• Search by typing song/artist name\n"
            "• Use inline mode: type @botusername in any chat\n"
        )
        
        await msg.answer(help_text, parse_mode=ParseMode.MARKDOWN)
        
        # Log the help command usage
        await log_action(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            action_type="help_command"
        )

    @dp.message(F.text.regexp(URL_PATTERN))
    async def handle_music_url(msg: types.Message):
        """Handle messages containing music URLs"""
        url = msg.text.strip()
        
        # Log the URL download action
        await log_action(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            action_type="url_download",
            url=url
        )
        
        # Send typing action while fetching song info
        await bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
        
        # Try to fetch song info from the URL
        song_info = await fetch_song_info(url)
        
        if song_info:
            # Create a message with song info
            message_text = await create_message_text(song_info)
            is_album = song_info.get('type') == 'album'
            
            if is_album:
                # For albums, just send the info without download functionality
                await msg.answer(
                    message_text,
                    link_preview_options=types.LinkPreviewOptions(
                        url=song_info['thumbnailUrl'], 
                        prefer_large_media=True, 
                        show_above_text=True
                    )
                )
            else:
                # For songs, send info and start downloading
                info_msg = await msg.answer(
                    message_text,
                    link_preview_options=types.LinkPreviewOptions(
                        url=song_info['thumbnailUrl'], 
                        prefer_large_media=True, 
                        show_above_text=True
                    ),
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="⏳ Downloading...", callback_data="downloading")]
                    ])
                )
                
                # Send upload_audio action while downloading
                await bot.send_chat_action(msg.chat.id, ChatAction.UPLOAD_VOICE)
                
                # Start downloading in background
                yt_url = song_info['platform_urls'].get('YTMusic')
                if yt_url:
                    await asyncio.create_task(download_and_send_audio_direct(
                        msg.chat.id, 
                        info_msg.message_id, 
                        yt_url, 
                        msg.from_user.id
                    ))
                else:
                    # Update button if no downloadable URL found
                    await info_msg.edit_reply_markup(
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text="❌ No downloadable source found", callback_data="download_error")]
                        ])
                    )
        else:
            await msg.answer("❌ Couldn't find information about this music link. Please try another URL.")

    @dp.message(F.text & ~F.text.regexp(URL_PATTERN) & ~F.text.startswith('/'))
    async def handle_music_search(msg: types.Message):
        """Handle messages containing search queries"""
        query = msg.text.strip()
        
        if len(query) < 2:
            await msg.answer("🔍 Please provide a longer search query (at least 2 characters).")
            return
        
        # Log the search query action
        await log_action(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            action_type="search_query",
            query=query
        )
        
        # Send typing action while searching
        await bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
        
        # Search on Spotify
        search_results = await search_spotify(query)
        
        if search_results:
            # Take the first result (most relevant)
            first_result = search_results[0]
            song_info = await fetch_song_info(first_result['url'])
            
            if song_info:
                # Create a message with song info
                message_text = await create_message_text(song_info)
                is_album = song_info.get('type') == 'album'
                
                if is_album:
                    # For albums, just send the info without download functionality
                    await msg.answer(
                        message_text,
                        link_preview_options=types.LinkPreviewOptions(
                            url=song_info['thumbnailUrl'], 
                            prefer_large_media=True, 
                            show_above_text=True
                        )
                    )
                else:
                    # For songs, send info and start downloading
                    info_msg = await msg.answer(
                        message_text,
                        link_preview_options=types.LinkPreviewOptions(
                            url=song_info['thumbnailUrl'], 
                            prefer_large_media=True, 
                            show_above_text=True
                        ),
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text="⏳ Downloading...", callback_data="downloading")]
                        ])
                    )
                    
                    # Send upload_audio action while downloading
                    await bot.send_chat_action(msg.chat.id, ChatAction.UPLOAD_VOICE)
                    
                    # Start downloading in background
                    yt_url = song_info['platform_urls'].get('YTMusic')
                    if yt_url:
                        await asyncio.create_task(download_and_send_audio_direct(
                            msg.chat.id, 
                            info_msg.message_id, 
                            yt_url, 
                            msg.from_user.id
                        ))
                    else:
                        # Update button if no downloadable URL found
                        await info_msg.edit_reply_markup(
                            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                [types.InlineKeyboardButton(text="❌ No downloadable source found", callback_data="download_error")]
                            ])
                        )
            else:
                await msg.answer("❌ Couldn't fetch detailed information about the found song.")
        else:
            await msg.answer(f"🔍 No results found for: '{query}'\n\nTry using different keywords or check the spelling.")

    @dp.callback_query(F.data == "download_error")
    async def handle_download_error(call: types.CallbackQuery):
        await call.answer("There was an error downloading the track. It might be too long or unavailable.", show_alert=True)

    @dp.callback_query(F.data == "download_success")
    async def handle_download_success(call: types.CallbackQuery):
        await call.answer("Track downloaded successfully! 🎵", show_alert=False)

    @dp.callback_query(F.data == "downloading")
    async def handle_downloading(call: types.CallbackQuery):
        await call.answer("Downloading in progress, please wait... ⏳", show_alert=False)

    @dp.callback_query()
    async def downloading_info(call: types.CallbackQuery):
        await call.answer(f"Downloading the track from {call.data}, please wait...", show_alert=True)

    @dp.chosen_inline_result()
    async def load_song(res: types.ChosenInlineResult):
        if re.match(URL_PATTERN, res.result_id) and '.link/' not in res.result_id:
            await asyncio.create_task(download_and_send_audio(res))

    return bot, dp

async def start_polling(bot, dp):
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)
