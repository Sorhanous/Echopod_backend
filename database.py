import json
import psycopg2
from psycopg2 import pool
from config import secrets  # Import secrets from config
from dotenv import load_dotenv
import os
from psycopg2 import sql
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Debugging information to check if .env is loaded correctly
#print("Loaded .env file")

ENV = 'e1'


#print("Environment Variable ENV:", ENV)

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
    maxconn=30,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    dbname=db_name
)

def get_db_connection():
    print("Getting DB connection")
    return db_pool.getconn()

def put_db_connection(connection):
    db_pool.putconn(connection)

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
                    print("Record updated successfully based on email.")
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
            print("New record inserted successfully.")

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
       # update_query = "UPDATE users SET url_count = url_count + 1 WHERE firebase_uid = %s;"
        with conn.cursor() as cur:
            # Increment url_count
          #  cur.execute(update_query, (firebase_uid,))
          #  conn.commit()
            
            # Get user_id
            cur.execute(query, (firebase_uid,))
            user_id = cur.fetchone()
            print(f"User ID: {user_id}")
        return user_id[0] if user_id else None
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
        return None
    
def get_user_id_by_ip(ip, conn):
    try:
        print(f"IP: {ip}")
        
        # Check for a record with the given IP and a non-null email
        query_with_email = "SELECT user_id FROM users WHERE user_ip = %s AND email IS NOT NULL;"
        with conn.cursor() as cur:
            cur.execute(query_with_email, (ip,))
            user_with_email = cur.fetchone()
        
        if user_with_email:
            return user_with_email[0]
        
        # If no record with a non-null email, check for a record with a null email
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
    print("Incrementing URL count")
    try:
       # print("Here we are: ", user_id)
        update_query = "UPDATE users SET url_count = url_count + 1 WHERE user_id = %s;"
        with conn.cursor() as cur:
            # Ensure user_id is passed as a tuple
            cur.execute(update_query, (int(user_id),))
            conn.commit()
            print("URL count incremented successfully")
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        conn.rollback()  # Roll back the transaction in case of error
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
            #print(existing_summary)
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
                #print("URL Count:", url_count[0])
                summ["url_count"] = url_count[0]
            else:
                print("URL Count not found for user_id:", link_data['user_id'])
            
            #print(summ)
            
            return True, summ
        
        return False, "Continue with processing"
    
    except psycopg2.DatabaseError as e:
        return False, str(e)
    
def get_url_count_by_ips(data, conn):
    try:
        ip = data.get('ip')
        current_user = data.get('currentUser')
        #print(">>>>>>>>>>>>>" , current_user)
        if current_user and current_user.get('email'):

            query = "SELECT url_count FROM users WHERE email = %s;"
            param = (current_user['email'],)
        else:
            query = "SELECT url_count FROM users WHERE user_ip = %s AND email IS NULL;"
            param = (ip,)
        
        #print("Query:", query)
        #print("Param:", param)
        
        with conn.cursor() as cur:
            cur.execute(query, param)
            url_count = cur.fetchone()
            #print(f"URL Count: {url_count}")
        
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
