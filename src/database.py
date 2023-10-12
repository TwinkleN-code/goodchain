import sqlite3

class Database:

    def __init__(self, db_name='users.db'):
        self.db_name = db_name

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def setup(self):
        self.execute(''' CREATE TABLE IF NOT EXISTS users (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT, 
                            username TEXT NOT NULL UNIQUE, 
                            password TEXT NOT NULL,
                            privatekey TEXT NOT NULL,
                            publickey TEXT NOT NULL)''')
        
    def _execute(self, query, params=None, fetch=False):
        with self._connect() as conn:
            c = conn.cursor()
            if params:
                c.execute(query, params)
            else:
                c.execute(query)
            if fetch:
                return c.fetchall()
            conn.commit()

    def execute(self, query, params=None):
        return self._execute(query, params)

    def fetch(self, query, params=None):
        return self._execute(query, params, fetch=True)