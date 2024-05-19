import json
import psycopg2
from psycopg2 import pool
from google.cloud import secretmanager


def access_secret_version(secret_id, version_id="latest"):
    """
    Access a secret version in Secret Manager.

    Args:
    project_id: Google Cloud project ID
    secret_id: ID of the secret to access
    version_id: version of the secret (default to "latest")

    Returns:
    Secret value as a string.
    """
    project_id = "dynamic-heading-419922"
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Return the payload as a string.
    return response.payload.data.decode("UTF-8")




# Retrieve your database secrets using the 'access_secret_version' function
db_user = "postgres"
db_password = "4J[]FTjbh_Io66gfZb()f4AqQDn~" #4J[]FTjbh_Io66gfZb()f4AqQDn~
db_host = "localhost"
db_name = "Bevi_DB"
# Initialize the connection pool
db_pool = pool.SimpleConnectionPool(minconn=1,
                                    maxconn=20,
                                    user="postgres",
                                    password="4J[]FTjbh_Io66gfZb()f4AqQDn~",
                                    host="brevydb.cluster-crg2yo8kmdio.us-west-2.rds.amazonaws.com",
                                    port=5434,
                                    dbname="bevi-db")


def get_db_connection():
  return db_pool.getconn()


def put_db_connection(connection):
  db_pool.putconn(connection)


def close_db_pool():
  db_pool.closeall()


def upsert_user(user_data, conn):
  # Prepare the base upsert query with placeholders for dynamic update parts
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

  # Initialize the update_parts list for conditionally updating certain fields
  update_parts = []

  # Check if 'active', 'free_trial', 'usage_count' are in user_data before adding them to the update_parts list
  conditional_fields = ['active', 'free_trial', 'usage_count']
  for field in conditional_fields:
    if field in user_data:
      update_parts.append(f"{field} = EXCLUDED.{field}")

  # Append the conditional update statements to the upsert_query if any are present
  if update_parts:
    upsert_query += ", " + ", ".join(update_parts)

  # Using a context manager for the cursor to ensure it's closed properly
  try:
    with conn.cursor() as cur:
      cur.execute(upsert_query, user_data)
    conn.commit(
    )  # Ensure the transaction is committed to make changes persistent
  except psycopg2.IntegrityError as e:  # Catching the IntegrityError which includes unique constraint violations
      if "users_email_key" in str(e):
          print("An account with this email already exists.")
      conn.rollback()  # Rollback the transaction on error
      raise  
  except psycopg2.DatabaseError as e:
    print(f"Database error: {e}")
    conn.rollback()  # Rollback the transaction on error
    raise  # Re-raise the exception to ensure that the calling function can handle it


def get_user_id_by_firebase_uid(firebase_uid, conn):
  print("let's call the user table")
  try:
    query = "SELECT user_id FROM users WHERE firebase_uid = %s;"
    with conn.cursor() as cur:
      cur.execute(query, (firebase_uid, ))
      user_id = cur.fetchone()
    print(user_id)
    print("user_id")
    return user_id[0] if user_id else None
  except psycopg2.DatabaseError as e:
    print(f"Database error: {e}")
    return None


def insert_youtube_link(link_data, conn):
  cur = None
  try:
    # Check if the YouTube link already exists for the user
    check_query = """
        SELECT 1 FROM youtubelinks
        WHERE video_url = %(video_url)s;
        """
    cur = conn.cursor()
    cur.execute(check_query, link_data)
    exists = cur.fetchone()

    if exists:
      print("Link already exists for this user.")
      return False, "Link already exists for this user."

    # If the link does not exist, proceed with the insertion
    insert_query = """
        INSERT INTO youtubelinks (
            user_id, video_url, channel_url, video_description, video_summary_json
        ) VALUES (
            %(user_id)s, %(video_url)s, 'placeholder_for_channel_url', 'placeholder_for_video_description', %(video_summary_json)s
        )
        """
    cur.execute(insert_query, link_data)
    conn.commit()
    return True, "Video link added successfully."

  except psycopg2.DatabaseError as e:
    print(f"Database error: {e}")
    if conn:
      conn.rollback()
    return False, str(e)

  finally:
    if cur is not None:
      cur.close()


def store_youtube_link_data(firebase_uid, youtube_url, video_summary):
  print(
      f"Storing YouTube link data for firebase_uid: {firebase_uid}, youtube_url: {youtube_url})"
  )
  conn = get_db_connection()
  user_id = get_user_id_by_firebase_uid(firebase_uid, conn)
  if not user_id:
    print("User not found")
    put_db_connection(conn)
    return {"error": "User not found"}, 404

  # Prepare link data for insertion
  link_data = {
      'user_id':
      user_id,
      'video_url':
      youtube_url,
      # Assuming video_summary is already a JSON string or convert it accordingly
      'video_summary_json':
      json.dumps(video_summary)
      if not isinstance(video_summary, str) else video_summary
  }

  try:
    insert_youtube_link(link_data, conn)
  except Exception as e:
    print(f"Error inserting YouTube link data: {e}")
    put_db_connection(conn)
    return {"error": str(e)}, 500

  put_db_connection(conn)
  return {"message": "Video processed and data stored successfully"}, 200


def get_or_process_video_link(link_data, conn):
  cur = None
  try:
    # Check if the YouTube link already exists for the user
    check_query = """
      SELECT video_summary_json FROM youtubelinks
      WHERE video_url = %(video_url)s;
      """
    cur = conn.cursor()
    cur.execute(check_query, link_data)
    existing_summary = cur.fetchone()

    if existing_summary:
      print("Link already exists for this user. Returning existing summary.")
      return True, existing_summary[
          0]  # Return the existing video_summary_json

    # If the link does not exist, proceed with the indicated "processing" logic
    # Note: The actual processing logic will likely be elsewhere,
    # but indicate here that processing should continue.
    return False, "Continue with processing"

  except psycopg2.DatabaseError as e:
    print(f"Database error: {e}")
    return False, str(e)

  finally:
    if cur:
      cur.close()
