import sqlite3
import logging
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                url TEXT,
                created_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def ad_exists(self, ad_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM ads WHERE id = ?', (str(ad_id),))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_ad(self, ad_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO ads (id, title, price, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(ad_data['id']),
                ad_data['title'],
                ad_data['price'],
                ad_data['url'],
                datetime.now()
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            logging.error(f"Erro ao salvar no banco: {e}")
        finally:
            conn.close()