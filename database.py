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
            
            # Create statistics table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS statistics
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action_type TEXT,
                    url TEXT,
                    query TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
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

async def log_action(user_id: int, username: str, action_type: str, url: str = None, query: str = None):
    """Log user actions for statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO statistics (user_id, username, action_type, url, query) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, action_type, url, query)
        )
        await db.commit()

async def get_bot_statistics():
    """Get comprehensive bot usage statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        
        # Total users
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM statistics") as cursor:
            result = await cursor.fetchone()
            stats['total_users'] = result[0] if result else 0
        
        # Total actions
        async with db.execute("SELECT COUNT(*) FROM statistics") as cursor:
            result = await cursor.fetchone()
            stats['total_actions'] = result[0] if result else 0
        
        # Actions by type
        async with db.execute("""
            SELECT action_type, COUNT(*) as count 
            FROM statistics 
            GROUP BY action_type 
            ORDER BY count DESC
        """) as cursor:
            stats['actions_by_type'] = await cursor.fetchall()
        
        # Top users by activity
        async with db.execute("""
            SELECT username, user_id, COUNT(*) as action_count 
            FROM statistics 
            WHERE username IS NOT NULL
            GROUP BY user_id 
            ORDER BY action_count DESC 
            LIMIT 10
        """) as cursor:
            stats['top_users'] = await cursor.fetchall()
        
        # Daily statistics for last 7 days
        async with db.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM statistics 
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp) 
            ORDER BY date DESC
        """) as cursor:
            stats['daily_stats'] = await cursor.fetchall()
        
        # Total downloads
        async with db.execute("SELECT COUNT(*) FROM downloads") as cursor:
            result = await cursor.fetchone()
            stats['total_downloads'] = result[0] if result else 0
        
        return stats
