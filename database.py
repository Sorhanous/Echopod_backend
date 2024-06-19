import json
import psycopg2
from psycopg2 import pool
from config import secrets  # Import secrets from config
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Debugging information to check if .env is loaded correctly
print("Loaded .env file")

ENV = 'e1'


print("Environment Variable ENV:", ENV)

if ENV =="e1":
    db_user = "postgres"
    db_password = "newpassword24"
    db_host = "localhost"
    db_name = "Bevi_DB"
    db_port = 5433
    
else:
    print("******Production Environment*******")
    db_user = secrets['DB_USER']
    db_password = secrets['DB_PASSWORD']
    db_host = secrets['DB_HOST']
    db_name = secrets['DB_NAME']
    db_port = 5432
# Database connection details
"""db_user = secrets['DB_USER']
db_password = secrets['DB_PASSWORD']
db_host = secrets['DB_HOST']
db_name = secrets['DB_NAME']
db_port = 5432"""

# Initialize the connection pool
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    dbname=db_name
)

def get_db_connection():
    return db_pool.getconn()

def put_db_connection(connection):
    db_pool.putconn(connection)

def close_db_pool():
    db_pool.closeall()

def upsert_user(user_data, conn):
    upsert_query = """
    INSERT INTO Users (
        firebase_uid, name, display_name, email, email_verified,
        photo_url, signup_datetime, last_login_datetime
    ) VALUES (
        %(firebase_uid)s, %(name)s, %(display_name)s, %(email)s, %(email_verified)s,
        %(photo_url)s, %(signup_datetime)s, %(last_login_datetime)s
    )
    ON CONFLICT (firebase_uid)
    DO UPDATE SET
        name = EXCLUDED.name,
        display_name = EXCLUDED.display_name,
        email = EXCLUDED.email,
        email_verified = EXCLUDED.email_verified,
        photo_url = EXCLUDED.photo_url,
        signup_datetime = EXCLUDED.signup_datetime,
        last_login_datetime = EXCLUDED.last_login_datetime
    """
    try:
        with conn.cursor() as cur:
            cur.execute(upsert_query, user_data)
        conn.commit()
    except psycopg2.IntegrityError as e:
        if "users_email_key" in str(e):
            print("An account with this email already exists.")
        conn.rollback()
        raise
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise

def get_user_id_by_firebase_uid(firebase_uid, conn):
    try:
        print(f"Firebase UID: {firebase_uid}")
        query = "SELECT user_id FROM users WHERE firebase_uid = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (firebase_uid,))
            user_id = cur.fetchone()
            print(f"User ID: {user_id}")
        return user_id[0] if user_id else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        return None

def insert_youtube_link(link_data, conn):
    try:
        check_query = """
        SELECT 1 FROM youtubelinks WHERE video_url = %(video_url)s;
        """
        with conn.cursor() as cur:
            cur.execute(check_query, link_data)
            exists = cur.fetchone()
        if exists:
            return False, "Link already exists for this user."

        insert_query = """
        INSERT INTO youtubelinks (
            user_id, video_url, channel_url, video_description, video_summary_json
        ) VALUES (
            %(user_id)s, %(video_url)s, 'placeholder_for_channel_url', 'placeholder_for_video_description', %(video_summary_json)s
        )
        """
        with conn.cursor() as cur:
            cur.execute(insert_query, link_data)
        conn.commit()
        return True, "Video link added successfully."
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False, str(e)

def store_youtube_link_data(firebase_uid, youtube_url, video_summary):
    conn = get_db_connection()
    print("Connection: ")
    print(conn)

    user_id = get_user_id_by_firebase_uid(firebase_uid, conn)
    if not user_id:
        put_db_connection(conn)
        return {"error": "User not found"}, 404

    link_data = {
        'user_id': user_id,
        'video_url': youtube_url,
        'video_summary_json': json.dumps(video_summary) if not isinstance(video_summary, str) else video_summary
    }

    try:
        insert_youtube_link(link_data, conn)
    except Exception as e:
        put_db_connection(conn)
        return {"error": str(e)}, 500

    put_db_connection(conn)
    return {"message": "Video processed and data stored successfully"}, 200

def get_or_process_video_link(link_data, conn):
    try:
        check_query = """
        SELECT video_summary_json FROM youtubelinks WHERE video_url = %(video_url)s;
        """
        with conn.cursor() as cur:
            cur.execute(check_query, link_data)
            existing_summary = cur.fetchone()
        if existing_summary:
            return True, existing_summary[0]
        return False, "Continue with processing"
    except psycopg2.DatabaseError as e:
        return False, str(e)
