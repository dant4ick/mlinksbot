import asyncio
from bot import init_bot, start_polling
from database import init_db

async def main():
    await init_db()
    bot, dp = init_bot()
    await start_polling(bot, dp)

if __name__ == '__main__':
    asyncio.run(main())
