import sqlite3

class Database:

    def __init__(self, db_name='users.db'):
        self.db_name = db_name

    def execute(self, query, params=None):
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            if params:
                c.execute(query, params)
            else:
                c.execute(query)

            conn.commit()
            return c
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def setup(self):
        self.execute(''' CREATE TABLE IF NOT EXISTS users ()
                        ID INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL''')
        
    def fetch(self, query, params=None):
        conn = None
        results = None
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            if params:
                c.execute(query, params)
            else:
                c.execute(query)

            results = c.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

        return results