import logging
import aiosqlite
from config import DB_PATH

async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS downloads
                (url TEXT PRIMARY KEY, file_id TEXT)
            ''')
            await db.commit()
    except aiosqlite.OperationalError as e:
        logging.error(f'Failed to create table (check if db file exists): {e}')
        if not DB_PATH.exists():
            logging.error('Database file does not exist, trying to create one...')
            DB_PATH.touch()
            await init_db()
            return
        else:
            logging.error('Database file exists, but failed to create table')
            

async def get_file_id(url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT file_id FROM downloads WHERE url = ?", (url,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def save_file_id(url: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO downloads (url, file_id) VALUES (?, ?)", (url, file_id))
        await db.commit()
