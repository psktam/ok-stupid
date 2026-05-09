from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3 as sql
from typing import Optional


@dataclass
class BlogEntry:
    create_date: datetime
    title: str
    id: Optional[int] = None

    def _create_date_as_str(self) -> str:
        return self.create_date.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def parse_create_date(cls, create_date_str: str) -> datetime:
        return datetime.strptime(create_date_str, "%Y-%m-%d %H:%M:%S")

    def blog_md_text(self, con: sql.Connection) -> str:
        cursor = con.cursor()
        cursor.execute(f"SELECT raw_text FROM blog_entries WHERE id={self.id}")
        return cursor.fetchone()[0]

    @classmethod
    def initialize_table(cls, con: sql.Connection):
        cursor = con.cursor()
        cursor.execute("""
        CREATE TABLE blog_entries(
            id INTEGER PRIMARY KEY ASC, 
            title TEXT,
            date TEXT,
            raw_text TEXT
        )""")
        con.commit()
        cursor.close()

    def insert_new_blog_entry(self, con: sql.Connection, text: str):
        cursor = con.cursor()
        cursor.execute(f"""
        INSERT INTO blog_entries(date, raw_text)
        VALUES('{self._create_date_as_str()}', '{text.replace("'", "''")}')
        """)
        self.id = cursor.lastrowid
        con.commit()
        cursor.close()

    def update_blog_entry(self, con: sql.Connection, text: str):
        cursor = con.cursor()
        cursor.execute(f"""
        UPDATE blog_entries 
        SET date='{self._create_date_as_str()}',
            raw_text='{text.replace("'", "''")}',
            title='{self.title}'
        WHERE id={self.id}
        """)
        con.commit()
        cursor.close()

    @classmethod
    def load(cls, con: sql.Connection, blog_id: int):
        cursor = con.cursor()
        cursor.execute(f"""
        SELECT title, date, raw_text FROM blog_entries WHERE id={blog_id}
        """)
        title, create_date_txt, raw_text = cursor.fetchone()
        cursor.close()
        return BlogEntry(
            create_date=cls.parse_create_date(create_date_txt), title=title, id=blog_id
        ), raw_text

    @classmethod
    def load_only_blog_entry(cls, con: sql.Connection, blog_id: int):
        cursor = con.cursor()
        cursor.execute(f"""
        SELECT title, date FROM blog_entries WHERE id={blog_id}
        """)
        title, create_date_txt = cursor.fetchone()
        cursor.close()
        return BlogEntry(
            create_date=cls.parse_create_date(create_date_txt), title=title, id=blog_id
        )


def get_sql_connection():
    return sql.connect(os.environ.get("DB_FNAME", "okstupid.db"))


def load_blog_entries(con: sql.Connection):
    cursor = con.cursor()
    cursor.execute("SELECT id, title, date FROM blog_entries")
    entries = cursor.fetchall()
    cursor.close()
    return [
        BlogEntry(id=db_id, title=title, create_date=BlogEntry.parse_create_date(date))
        for (db_id, title, date) in entries
    ]
