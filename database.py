import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS downloads
            (url TEXT PRIMARY KEY, file_id TEXT)
        ''')
        await db.commit()

async def get_file_id(url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT file_id FROM downloads WHERE url = ?", (url,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def save_file_id(url: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO downloads (url, file_id) VALUES (?, ?)", (url, file_id))
        await db.commit()
