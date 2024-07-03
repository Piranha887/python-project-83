import os
import sys

import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('HOST'),
            port=os.getenv('PORT'),
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            database=os.getenv('DATABASE')
        )
        print("Успешно подключено к базе данных PostgreSQL.")
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка при подключении к базе данных PostgreSQL: {e}")
        sys.exit(1)


def get_url_by_id(id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("""
                SELECT name, created_at
                FROM urls
                WHERE id = %s""", [id])
            return cur.fetchone()


def get_url_checks_by_id(id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("""
                SELECT id, created_at, status_code, h1, title, description
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC""", [id])
            return cur.fetchall()


def add_url(valid_url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO urls (name)
                VALUES (%s) RETURNING id""", [valid_url])
            url_id = cur.fetchone()[0]
            conn.commit()
        return url_id


def get_url_id_by_name(valid_url):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("""
                SELECT id FROM urls
                WHERE name = %s""", [valid_url])
            return cur.fetchone()


def get_all_urls():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("""
                SELECT
                DISTINCT ON (urls.id) urls.id, urls.name, MAX(url_checks.created_at), url_checks.status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id, url_checks.status_code
                ORDER BY urls.id DESC""")
            return cur.fetchall()


def add_url_check(id, status_code, h1, title, meta):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (url_id, status_code, h1, title, description)
                VALUES (%s, %s, %s, %s, %s)""", [
                id, status_code, h1, title, meta])
            conn.commit()
