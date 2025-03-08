import duckdb

class DatabaseManager:
    def __init__(self, db_file='music.db'):
        self.conn = duckdb.connect(db_file)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                title VARCHAR,
                artist VARCHAR,
                album VARCHAR,
                file_path VARCHAR
            )
        """)

    def add_song(self, title, artist, album, file_path):
        self.conn.execute("""
            INSERT INTO songs (title, artist, album, file_path)
            VALUES (?, ?, ?, ?)
        """, (title, artist, album, file_path))

    def get_songs(self):
        return self.conn.execute("SELECT * FROM songs").fetchall()
