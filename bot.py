import asyncio
import logging
import re
import sys
from aiogram import Dispatcher, F, filters, types
from aiogram.enums import ParseMode
from aiogram.methods.delete_webhook import DeleteWebhook
from config import URL_PATTERN
from spotify import search_spotify, fetch_song_info
from youtube import download_and_send_audio
from utils import generate_inline_query_results
from shared import bot

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def init_bot():
    dp = Dispatcher()

    @dp.inline_query(F.query.regexp(URL_PATTERN))
    async def search_song(inline_query: types.InlineQuery):
        query = inline_query.query
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
            f"👋 Hello! Here's how to use me in inline query mode:\n"
            f"1️⃣ Type the bot's username in any chat, followed by a space.\n"
            f"2️⃣ Paste the URL of the song you want to share. For example: `@{bot_info.username} https://www.youtube.com/watch?v=P_bPsPp_f1k`\n"
            f"3️⃣ You'll see a preview of the song information. Tap on it to send it to your chat.\n\n"
            f"🚀 Try it out now!"
        )
        await msg.answer(tutorial_message, parse_mode=ParseMode.MARKDOWN)

    @dp.callback_query(F.data == "download_error")
    async def handle_download_error(call: types.CallbackQuery):
        await call.answer("There was an error downloading the track. It might be too long or unavailable.", show_alert=True)

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
