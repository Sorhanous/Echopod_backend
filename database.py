import json, time
import psycopg2
from psycopg2 import pool
from config import secrets  # Import secrets from config
from dotenv import load_dotenv
import os
from psycopg2 import sql
from datetime import datetime
from contextlib import contextmanager
import threading
from psycopg2.pool import ThreadedConnectionPool

# Load environment variables from .env file
load_dotenv()

ENV = 'e3'

if ENV =="e1":
    db_user = "postgres"
    db_password = "newpassword24"
    db_host = "localhost"
    db_name = "Bevi_DB"
    db_port = 5433
    
else:
    db_user = secrets['DB_USER']
    db_password = secrets['DB_PASSWORD']
    db_host = secrets['DB_HOST']
    db_name = secrets['DB_NAME']
    db_port = 5432

connection_usage = {}
# Initialize the connection pool
db_pool = ThreadedConnectionPool(
    minconn=20,     # Increased minimum connections
    maxconn=100,    # Increased maximum connections
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    dbname=db_name
)

@contextmanager
def get_connection_context():
    """
    Context manager for safe handling of database connections
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        if not conn.closed:
            conn.commit()
    except Exception as e:
        if conn and not conn.closed:
            conn.rollback()
        raise e
    finally:
        if conn and not conn.closed:
            put_db_connection(conn)

def get_db_connection():
    """
    Get a connection from the pool with retry logic
    """
    max_retries = 3
    retry_delay = 0.1  # 100ms
    
    for attempt in range(max_retries):
        try:
            conn = db_pool.getconn(key=id(threading.current_thread()))
            connection_usage[conn] = time.time()
            return conn
        except pool.PoolError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise

def put_db_connection(conn):
    """
    Return a connection to the pool with safety checks
    """
    if conn and not conn.closed:
        try:
            db_pool.putconn(conn, key=id(threading.current_thread()))
        except Exception as e:
            print(f"Error returning connection to pool: {e}")
            try:
                conn.close()
            except:
                pass

def close_db_pool():
    db_pool.closeall()

def upsert_user(user_data, conn):
    # Ensure all required keys are present and properly set in user_data
    required_keys = [
        'user_ip', 'firebase_uid', 'name', 'display_name', 'email', 'email_verified',
        'photo_url', 'signup_datetime', 'last_login_datetime', 'active', 'free_trial'
    ]

    for key in required_keys:
        if key not in user_data:
            user_data[key] = None

    # Convert boolean to integer for active and free_trial fields
    user_data['active'] = 1 if user_data['active'] else 0
    user_data['free_trial'] = 1 if user_data['free_trial'] else 0

    # Ensure email and user_ip are not empty
    if user_data['email'] == '':
        user_data['email'] = None
    if user_data['user_ip'] == '':
        user_data['user_ip'] = None

    # Ensure signup_datetime and last_login_datetime have valid values
    if user_data['signup_datetime'] is None or user_data['signup_datetime'] == '':
        user_data['signup_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if user_data['last_login_datetime'] is None or user_data['last_login_datetime'] == '':
        user_data['last_login_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Check conditions
    if user_data['email'] is None and user_data['user_ip'] is None:
        print("Both email and user_ip are NULL. No action taken.")
        return

    try:
        with conn.cursor() as cur:
            # Check for existing user based on email if email is provided
            if user_data['email'] is not None:
                cur.execute("SELECT user_id FROM Users WHERE email = %s", (user_data['email'],))
                result = cur.fetchone()
                if result:
                    existing_user_id = result[0]
                    update_query = """
                    UPDATE Users
                    SET user_ip = %s, firebase_uid = %s, name = %s, display_name = %s, email_verified = %s,
                        photo_url = %s, signup_datetime = %s, last_login_datetime = %s, active = %s, free_trial = %s
                    WHERE user_id = %s
                    """
                    cur.execute(update_query, (
                        user_data['user_ip'], user_data['firebase_uid'], user_data['name'], user_data['display_name'],
                        user_data['email_verified'], user_data['photo_url'], user_data['signup_datetime'],
                        user_data['last_login_datetime'], user_data['active'], user_data['free_trial'], existing_user_id
                    ))
                    conn.commit()
                    return
            
            # Check for existing user based on user_ip if email is not provided
            if user_data['email'] is None and user_data['user_ip'] is not None:
                cur.execute("SELECT user_id, email FROM Users WHERE user_ip = %s", (user_data['user_ip'],))
                result = cur.fetchone()
                if result:
                    existing_user_id, existing_email = result
                    if existing_email is None:
                        update_query = """
                        UPDATE Users
                        SET firebase_uid = %s, name = %s, display_name = %s, email_verified = %s,
                            photo_url = %s, signup_datetime = %s, last_login_datetime = %s, active = %s, free_trial = %s
                        WHERE user_id = %s
                        """
                        cur.execute(update_query, (
                            user_data['firebase_uid'], user_data['name'], user_data['display_name'],
                            user_data['email_verified'], user_data['photo_url'], user_data['signup_datetime'],
                            user_data['last_login_datetime'], user_data['active'], user_data['free_trial'], existing_user_id
                        ))
                        conn.commit()
                        print("Record updated successfully based on user_ip with no email.")
                        return
                    else:
                        print("Record with this user_ip already exists and has an email. No action taken.")
                        return
            
            # Insert new user if no existing user is found
            insert_query = """
            INSERT INTO Users (
                user_ip, firebase_uid, name, display_name, email, email_verified, photo_url, signup_datetime,
                last_login_datetime, active, free_trial
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (
                user_data['user_ip'], user_data['firebase_uid'], user_data['name'], user_data['display_name'],
                user_data['email'], user_data['email_verified'], user_data['photo_url'], user_data['signup_datetime'],
                user_data['last_login_datetime'], user_data['active'], user_data['free_trial']
            ))
            conn.commit()

    except psycopg2.IntegrityError as e:
        conn.rollback()
        error_message = str(e)
        print(f"IntegrityError: {error_message}")
        raise
    except psycopg2.Error as e:
        conn.rollback()
        error_message = str(e)
        print(f"DatabaseError: {error_message}")
        raise
    except Exception as e:
        conn.rollback()
        error_message = str(e)
        print(f"UnexpectedError: {error_message}")
        raise

def get_url_count_by_id(id, conn):
    try:
        query = "SELECT url_count FROM users WHERE user_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (id,))
            url_count = cur.fetchone()
        return url_count[0] if url_count else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None
    
def get_user_id_by_firebase_uid(firebase_uid, conn):
    try:
        query = "SELECT user_id FROM users WHERE firebase_uid = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (firebase_uid,))
            user_id = cur.fetchone()
        return user_id[0] if user_id else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None
    
def get_user_id_by_ip(ip, conn):
    try:
        query_with_email = "SELECT user_id FROM users WHERE user_ip = %s AND email IS NOT NULL;"
        with conn.cursor() as cur:
            cur.execute(query_with_email, (ip,))
            user_with_email = cur.fetchone()
        
        if user_with_email:
            return user_with_email[0]
        
        query_without_email = "SELECT user_id FROM users WHERE user_ip = %s AND email IS NULL;"
        with conn.cursor() as cur:
            cur.execute(query_without_email, (ip,))
            user_without_email = cur.fetchone()
        
        return user_without_email[0] if user_without_email else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None

def increment_url_count(user_id, conn):
    try:
        if conn.closed:
            print("Connection is closed. Cannot proceed.")
            return None

        # Get current count
        with conn.cursor() as cur:
            cur.execute("SELECT url_count FROM users WHERE user_id = %s;", (int(user_id),))
            current_count = cur.fetchone()[0]
            print(f"[DEBUG] Current count before increment: {current_count}")

        # Proceed with updating the URL count
        update_query = "UPDATE users SET url_count = url_count + 1 WHERE user_id = %s;"
        with conn.cursor() as cur:
            cur.execute(update_query, (int(user_id),))
            conn.commit()
            
            # Get new count
            cur.execute("SELECT url_count FROM users WHERE user_id = %s;", (int(user_id),))
            new_count = cur.fetchone()[0]
            print(f"[DEBUG] New count after increment: {new_count}")
    
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        print("Rolling back the transaction due to the error.")
        conn.rollback()  # Roll back the transaction in case of error
        return None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Rolling back the transaction due to the unexpected error.")
        conn.rollback()  # Roll back the transaction in case of error
        return None

    finally:
        # Return the connection to the pool
        db_pool.putconn(conn)

def insert_youtube_link(link_data, conn):
    try:
        print(f"Received link_data: {link_data}")
        
        check_query = """
        SELECT 1 FROM youtubelinks WHERE video_url = %(video_url)s;
        """
        with conn.cursor() as cur:
            cur.execute(check_query, link_data)
            exists = cur.fetchone()
        if exists:
            return True, "Video link already exists"

        # Dynamically build the insert query based on available fields
        available_fields = []
        values = []
        for field in ['user_id', 'video_url', 'channel_url', 'video_description', 
                     'video_summary_json', 'title', 'default_thumbnail', 
                     'medium_thumbnail', 'channel_name', 'published_date']:
            if field in link_data:
                available_fields.append(field)
                values.append(f'%({field})s')

        insert_query = f"""
        INSERT INTO youtubelinks (
            {', '.join(available_fields)}
        ) VALUES (
            {', '.join(values)}
        )
        """
        
        with conn.cursor() as cur:
            cur.execute(insert_query, link_data)
        conn.commit()
        return True, "Video link added successfully."
    except Exception as e:
        print(f"Error in insert_youtube_link: {str(e)}")
        conn.rollback()
        return False, str(e)

def store_youtube_link_data(user_id, youtube_url, video_summary):
    conn = get_db_connection()
    try:
       #user_id = get_user_id_by_firebase_uid(firebase_uid, conn)
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
            # Get the link_id of the newly created entry
            with conn.cursor() as cur:
                cur.execute("SELECT link_id FROM youtubelinks WHERE video_url = %s", (youtube_url,))
                link_id = cur.fetchone()[0]
            conn.commit()
            return {"message": "Video processed and data stored successfully", "link_id": link_id}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    finally:
        put_db_connection(conn)  # Ensure connection is always returned to the pool

def get_or_process_video_link(link_data, conn):
    try:
        # Check if video summary already exists
        check_query = """
        SELECT video_summary_json, link_id FROM youtubelinks WHERE video_url = %(video_url)s;
        """
        with conn.cursor() as cur:
            cur.execute(check_query, link_data)
            existing_summary = cur.fetchone()
        
        if existing_summary:
            print("Summary already exists for this video.")
            summ = {
                "summary": existing_summary[0],
                "link_id": existing_summary[1]
            }
            
            # Fetch url_count for the user
            url_count_query = "SELECT url_count FROM users WHERE user_id = %(user_id)s;"
            with conn.cursor() as cur:
                cur.execute(url_count_query, {'user_id': link_data['user_id']})
                url_count = cur.fetchone()
            
            if url_count:
                summ["url_count"] = url_count[0]
            else:
                print("URL Count not found for user_id:", link_data['user_id'])
            
            print(summ)
            
            return True, summ
     
        return False, "Continue with processing"
    
    except psycopg2.DatabaseError as e:
        conn.rollback() 
        return False, str(e)
        
def get_url_count_by_ips(data, conn):
    try:
        ip = data.get('ip')
        current_user = data.get('currentUser')
        if current_user and current_user.get('email'):
            query = "SELECT url_count FROM users WHERE email = %s;"
            param = (current_user['email'],)
        else:
            query = "SELECT url_count FROM users WHERE user_ip = %s AND email IS NULL;"
            param = (ip,)
        
        with conn.cursor() as cur:
            cur.execute(query, param)
            url_count = cur.fetchone()
        
        return url_count[0] if url_count else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None

def has_email_by_ip(ip, conn):
    try:
        query = "SELECT 1 FROM users WHERE user_ip = %s AND email IS NOT NULL;"
        with conn.cursor() as cur:
            cur.execute(query, (ip,))
            result = cur.fetchone()
        return result is not None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False

def update_total_time_saved(user_email, time_saved, conn):
    try:
        print("*******************************Updating total time saved for user_id:", str(time_saved))
        update_query = "UPDATE users SET total_time_saved = total_time_saved + %s WHERE email = %s;"
        with conn.cursor() as cur:
            cur.execute(update_query, (time_saved, user_email))
            conn.commit()
            print("Total time saved updated successfully")
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None
    finally:
        if conn:
            db_pool.putconn(conn)

def get_total_time_saved_by_email(user_email, conn):
    try:
        query = "SELECT total_time_saved FROM users WHERE email = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (user_email,))
            total_time_saved = cur.fetchone()
        return total_time_saved[0] if total_time_saved else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None

def get_video_details(conn, limit=15):
    """
    Fetches video details needed for the frontend display.
    Returns: list of dictionaries containing video information
    """
    try:
        query = """
        SELECT 
            video_url,
            title,
            default_thumbnail,
            medium_thumbnail,
            channel_name,
            TO_CHAR(published_date, 'Mon DD, YYYY') as published_date
        FROM youtubelinks
        ORDER BY published_date DESC
        LIMIT %s;
        """
        
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            columns = [desc[0] for desc in cur.description]
            videos = []
            for row in cur.fetchall():
                video_dict = dict(zip(columns, row))
                # Ensure all required fields are present, even if null
                video_dict.setdefault('youtube_url', None)
                video_dict.setdefault('title', 'Untitled Video')
                video_dict.setdefault('default_thumbnail', None)
                video_dict.setdefault('channel_name', 'Unknown Channel')
                video_dict.setdefault('published_date', 'Unknown date')
                videos.append(video_dict)
            
            return videos
            
    except Exception as e:
        print(f"Error fetching videos: {e}")
        raise

def get_pool_status():
    """
    Get current status of the connection pool
    """
    return {
        "used_connections": len(db_pool._used),
        "free_connections": len(db_pool._pool),
        "total_connections": len(db_pool._pool) + len(db_pool._used)
    }

def cleanup_stale_connections():
    """
    Clean up any stale connections in the pool
    """
    try:
        with get_connection_context() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        print(f"Error in connection cleanup: {e}")

def start_cleanup_timer():
    cleanup_thread = threading.Thread(target=cleanup_stale_connections, daemon=True)
    cleanup_thread.start()

import atexit

# Register cleanup on shutdown
atexit.register(close_db_pool)

# Start the cleanup timer
start_cleanup_timer()
