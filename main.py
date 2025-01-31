from flask import Flask, jsonify, request 
import requests
import datetime
import json
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import openai
import re
from google.cloud import secretmanager
from prompts import structured_prompt
from create_database import generate_data_store
from transcribe import youtube_transcriber
from functions import combine_jsons
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.discovery import build
from database import db_pool, insert_youtube_link, get_video_details, update_total_time_saved, get_total_time_saved_by_email, get_db_connection, has_email_by_ip, put_db_connection, increment_url_count, get_url_count_by_id, get_url_count_by_ips,  get_user_id_by_ip, upsert_user, get_or_process_video_link, get_user_id_by_firebase_uid
from config import secrets  
from query_data import query_data
import stripe 
from playlist import extract_video_ids_from_youtube
from flask import Flask, request, jsonify
from contextlib import contextmanager
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    

# Retrieve and set the OPENAI_API_KEY and other secrets
try:
    Youtube_API_KEY_2 = secrets['YOUTUBE_API_KEY_2']
except KeyError:
    Youtube_API_KEY_2 = 'AIzaSyAQbjFNKS2AqqtY-gb4uuFr4AD_xeMx5_U'
#print(Youtube_API_KEY_2)

OPENAI_API_KEY = secrets.get('OPENAI_API_KEY')
OPENAI_API_SECRET_2 = secrets.get('OPENAI_API_SECRET_2')
Model3 = secrets.get('Model3')
Model4 = secrets.get('Model4')
stripe.api_key = secrets.get('Stripe_API_KEY')

#print(stripe.api_key)

proxies_list = {
    'http': 'http://sp6hfygjve:UnvAe7wcT5Z8n_wv7x@state.smartproxy.com:10000',
    'https': 'http://sp6hfygjve:UnvAe7wcT5Z8n_wv7x@state.smartproxy.com:10000'
    
}



def get_transcript_with_rotation(video_id, proxies_list):
    logger.info("Starting get_transcript_with_rotation")
    try:
        proxies = [proxies_list] if isinstance(proxies_list, dict) else proxies_list
        logger.info(f"Proxies type: {type(proxies)}")
        
        for proxy in proxies:
            try:
                logger.info(f"Trying proxy: {proxy}")
                print("video_id")
                print(video_id)
                transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxy)
                logger.info(f"Raw transcript type: {type(transcript)}")
                logger.info(f"First item of raw transcript: {transcript[0] if transcript else 'empty'}")
                
                if transcript and isinstance(transcript, list):
                    formatted_transcript = [{
                        'text': item.get('text', ''),
                        'start': item.get('start', 0)
                    } for item in transcript]
                    logger.info("Successfully formatted transcript")
                    return formatted_transcript
                
            except Exception as e:
                logger.error(f"Proxy attempt failed: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Transcript retrieval failed: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise

client = openai.OpenAI(api_key=OPENAI_API_KEY)
client_2 = openai.OpenAI(api_key=OPENAI_API_SECRET_2)
app = Flask(__name__)
app.register_blueprint(youtube_transcriber)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "https://bevi.ai", "*", "https://api.bevi.ai", "http://127.0.0.1:8080"],
                                  "supports_credentials": True}})

def call_api_in_parallel(prompts, apimodel, app):
    responses = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_prompt = {
            executor.submit(call_openai_api_with_context, prompt, apimodel, app): prompt
            for prompt in prompts
        }
        for future in as_completed(future_to_prompt):
            try:
                response = future.result()  # Assume this now returns a dict
                responses.append(response)
            except Exception as exc:
                print(f"API call generated an exception: {exc}")
    return responses  # Make sure this is defined and returned correctly

def call_openai_api_with_context(prompt, apimodel, app):
    with app.app_context():
        return call_openai_api(prompt, apimodel)

# Initial call:
def call_openai_api(_prompt, apimodel: str = "gpt-4o"):
    try:
        completion = client.chat.completions.create(model=apimodel,
                                                    temperature=1,
                                                    messages=[{
                                                        "role": "system",
                                                        "content": _prompt
                                                    }])
        response_contents = completion.choices[0].message.content
        if response_contents:
            response_content = response_contents.replace("```json", "").replace("```", "")
        else:
            raise ValueError("response_contents is None or not in the expected format.")

        if response_content:
            response_dict = json.loads(response_content)
            return response_dict  # Return a Python dict directly
        else:
            return {"error": "Response content is empty."}
    except Exception as e:
        return {"error": str(e)}

def remove_fillers(text):
    fillers = [" uh", " um", " ah", "uh ", " um ", " uh "]
    for filler in fillers:
        text = text.replace(filler, " ")
    return text

@app.route('/')
def health_check():
    return 'I am Healthy :)'


@app.route('/api/query_data', methods=['POST'])
def query_data_api():
    data = request.get_json()
   
    
    if not data or 'query' not in data:
        return jsonify({"error": "Query text is required"}), 400
    
    query_text = data['query']
    video_id = data.get('videoId', None)  # Extract videoId from the request data, default to None if not provided
    conversation = data.get('conversation', [])  # Extract conversation from the request data, default to an empty list if not provided
    chroma_path = data.get('chromaPath', None)  # Extract chroma_path from the request data, default to None if not provided
    yt_transcript = data.get('transcript_chunk', None)  # Extract transcript from the request data, default to None if not provided
    #print("HERE IS TRANSCRIT Length:")
   # print(len(yt_transcript))
    response = query_data(query_text, video_id, conversation, chroma_path, client, yt_transcript)  # Pass query_text, video_id, conversation, and chroma_path to the query_data function
    return jsonify(response)



    
@app.route('/api/search_youtube', methods=['POST'])
def search_youtube():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        google_api_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&maxResults=10&key={Youtube_API_KEY_2}'
        response = make_proxied_request(google_api_url, proxies_list)
        print("Google API response status code:", response.status_code)
        response_data = response.json()
        
        video_details = []
        for item in response_data.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            thumbnails = snippet['thumbnails']
            published_date = datetime.datetime.strptime(snippet['publishTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%b %d, %Y')
            video_details.append({
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                "title": snippet['title'],
                "default_thumbnail": thumbnails.get('high', {}).get('url'),
                "medium_thumbnail": thumbnails.get('medium', {}).get('url'),
                "channel_name": snippet['channelTitle'],
                "published_date": published_date,
            })
        
        return jsonify(video_details), 200
    except Exception as e:
        logger.error(f"Exception in search_youtube: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_latest_news', methods=['POST'])
def get_latest_news():
    queries = ["meme coins", "Joe rogan", "bitcoin", "War", "AI", "Trending News"]
    news_details = {query: [] for query in queries}

    try:
        for query in queries:
            google_api_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&maxResults=3&order=date&key={Youtube_API_KEY_2}'
            response = requests.get(google_api_url)
            print("Google API response status code:", response.status_code)
            response_data = response.json()
            #print("Google API response data:", response_data)
            
            for item in response_data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                thumbnails = snippet['thumbnails']
                published_date = datetime.datetime.strptime(snippet['publishTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%b %d, %Y')
                
                news_details[query].append({
                    "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": snippet['title'],
                    "default_thumbnail": thumbnails.get('high', {}).get('url'),
                    "medium_thumbnail": thumbnails.get('medium', {}).get('url'),
                    "channel_name": snippet['channelTitle'],
                    "published_date": published_date,
                    #"duration": "N/A"  # Duration is not available in search results
                })
        
        # Take a few from each topic, shuffle them, then return the list
        combined_news_details = []
        for query in queries:
            combined_news_details.extend(news_details[query][:5])  # Take first 5 from each topic
        
        import random
        random.shuffle(combined_news_details)
        
        return jsonify(combined_news_details), 200
    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_youtube_comments', methods=['POST'])
def get_youtube_comments():
    logger.info('Starting get_youtube_comments function')
    data = request.get_json()
    video_id = data.get('video_id')
    
    if not video_id:
        logger.error('Error: No video ID provided')
        return jsonify({"error": "Video ID is required"}), 400

    try:
        google_api_url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={Youtube_API_KEY_2}&order=relevance&maxResults=30'
        response = make_proxied_request(google_api_url, proxies_list)
        logger.info(f"Google API response status code: {response.status_code}")
        response_data = response.json()
        
        comments = []
        for item in response_data.get('items', []):
            comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment_text)
        
      #  print(f"Number of comments retrieved: {len(comments)}")
        
        # Create a prompt for OpenAI API
        prompt = f"""Analyze the following YouTube comments and provide a summary of:
            1. The overall tone of the comments people made about the speaker, video or topic (positive, negative, or neutral) and a brief explanation of why.
            2. The main topics or themes discussed, each with a short description.
            3. The most common opinions or viewpoints expressed across the comments.

            Comments:
            {comments}

            Please format your response as a JSON object with the following structure:
            the descriptions need to be conclusions of the topic rathr than topic summaries. 
            {{
                "sentiment": "Brief summary of the overall sentiment and rationale. 2-3 sentences max. brevity.",
                "topics": [
                    {{"topic": "Topic 1", "description": "Short description of Topic 1"}},
                    {{"topic": "Topic 2", "description": "Short description of Topic 2"}},
                    ...
                ],
                "summary": "A concise summary of the main viewpoints and discussions from the comments."
            }}
            """

        # Call OpenAI API to analyze comments
        try:
            print("Calling OpenAI API")
            response = client.chat.completions.create(
                model="gpt-4",  # Changed from "gpt-4o" to "gpt-4"
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = json.loads(response.choices[0].message.content)
            print("OpenAI API call successful")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print(f"Raw response content: {response.choices[0].message.content}")
            analysis = {"error": "Failed to parse OpenAI response"}
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            analysis = {"error": "Failed to analyze comments"}

        return jsonify({"analysis": analysis}), 200
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract_video_ids', methods=['POST'])
def extract_video_ids():
    logger.info("Starting extract_video_ids endpoint")
    
    data = request.get_json()
    youtube_url = data.get('youtube_url')
    logger.info(f"Received youtube_url: {youtube_url}")
    
    if not youtube_url:
        logger.error("No youtube_url provided in request")
        return jsonify({"error": "youtube_url is required"}), 400

    try:
        logger.info("Attempting to extract video IDs from YouTube URL")
        video_ids = extract_video_ids_from_youtube(youtube_url)
        logger.info(f"Extracted video IDs: {video_ids}")
        
        extracted_video_id = extract_video_id(youtube_url)
        logger.info(f"Main video ID extracted: {extracted_video_id}")
        
        if extracted_video_id in video_ids:
            video_ids.remove(extracted_video_id)
            logger.info(f"Removed main video ID from list. Remaining IDs: {video_ids}")
            
        if len(video_ids) == 1:
            video_ids_str = video_ids[0]
        else:
            video_ids_str = ','.join(video_ids)
        logger.info(f"Final video IDs string: {video_ids_str}")
            
        google_api_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_ids_str}&key={Youtube_API_KEY_2}'
        logger.info("Making request to Google API")
        logger.info(f"Google API URL: {google_api_url}")
        
        response = make_proxied_request(google_api_url, proxies_list)
        logger.info(f"Google API response status code: {response.status_code}")
        
        response_data = response.json()
        logger.debug(f"Google API response data: {response_data}")
        
        video_details = []
        logger.info("Processing video details from response")
        
        for item in response_data.get('items', []):
            try:
                logger.info(f"Processing video ID: {item['id']}")
                
                video_id = item['id']
                snippet = item['snippet']
                thumbnails = snippet['thumbnails']
                duration = item['contentDetails']['duration']
                logger.debug(f"Raw duration format: {duration}")
                
                # Handle different duration formats
                duration_str = ""
                logger.info("Attempting to parse duration")
                try:
                    if duration == "P0D":
                        duration_str = "0:00:00"
                        logger.debug("Handling P0D duration format")
                    else:
                        # Parse ISO 8601 duration format
                        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                        if match:
                            hours = int(match.group(1) or 0)
                            minutes = int(match.group(2) or 0)
                            seconds = int(match.group(3) or 0)
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            logger.debug(f"Parsed ISO 8601 duration: {duration_str}")
                        else:
                            logger.warning(f"Could not parse duration format: {duration}")
                            duration_str = duration
                except Exception as e:
                    logger.error(f"Error parsing duration: {str(e)}")
                    duration_str = duration

                published_date = datetime.datetime.strptime(snippet['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%b %d, %Y')
                logger.debug(f"Formatted published date: {published_date}")
                
                # Check for thumbnail availability
                thumbnail_url = None
                if 'maxres' in thumbnails:
                    thumbnail_url = thumbnails['maxres']['url']
                    logger.debug("Using maxres thumbnail")
                elif 'high' in thumbnails:
                    thumbnail_url = thumbnails['high']['url']
                    logger.debug("Using high thumbnail")
                else:
                    logger.warning("No high-quality thumbnail found")
                
                video_details.append({
                    "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": snippet['title'],
                    "default_thumbnail": thumbnail_url,
                    "medium_thumbnail": thumbnails['medium']['url'],
                    "channel_name": snippet['channelTitle'],
                    "published_date": published_date,
                    "duration": duration_str
                })
                logger.info(f"Successfully processed video ID: {video_id}")
                
            except KeyError as ke:
                logger.error(f"KeyError while processing video details: {ke}")
                logger.error(f"Item structure: {item}")
                continue
                
        logger.info(f"Successfully processed {len(video_details)} videos")
        return jsonify(video_details), 200
        
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_total_time_saved', methods=['POST'])
def get_total_time_saved():
    data = request.get_json()
    user_email = data.get('user_email')
    if not user_email:
        return jsonify({"error": "Email is required"}), 400

    try:
        with get_db_connection_context() as conn:
            total_time_saved_seconds = get_total_time_saved_by_email(user_email, conn)
            if total_time_saved_seconds is None:
                return jsonify({"error": "No time saved data found for the given email"}), 404

            hours = total_time_saved_seconds // 3600
            minutes = (total_time_saved_seconds % 3600) // 60
            response_string = f"{hours} Hrs {minutes} Mins"
            
            return jsonify({"total_time_saved": response_string}), 200
    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract_video_details', methods=['POST'])
def extract_video_data():
    data = request.get_json()
    video_id = data.get('video_id')
    user_email = data.get('user_email')
    logger.info(f"Extracted video_id: {video_id}")
    
    if not video_id:
        return jsonify({"error": "video_id is required"}), 400

    try:
        google_api_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_id}&key={Youtube_API_KEY_2}'
        logger.info("Google API URL: %s", google_api_url)
        
        response = make_proxied_request(google_api_url, proxies_list)
        logger.info("Google API response status code: %s", response.status_code)
        response_data = response.json()

        if 'items' not in response_data or not response_data['items']:
            logger.warning("No video details found in response data")
            return jsonify({"error": "No video details found"}), 404
        
        video_details = response_data['items'][0]
        snippet = video_details.get('snippet', {})
        content_details = video_details.get('contentDetails', {})
        duration = content_details.get("duration")
        try:
            # Function to convert ISO 8601 duration to seconds-=0p-`2[]`
            def iso8601_to_seconds(duration):
                print(f"Converting duration: {duration}")
                match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                if not match:
                    print("No match found for duration format")
                    return 0
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
            
            duration_seconds = iso8601_to_seconds(duration)
            print(f"Duration in seconds: {duration_seconds}")
            if user_email:
                conn = get_db_connection()
                update_total_time_saved(user_email, duration_seconds, conn)
            result = {
                "title": snippet.get("title"),
                #"description": snippet.get("description"),
                "thumbnails": {
                    "default": snippet.get("thumbnails", {}).get("default", {}).get("url"),
                    "medium": snippet.get("thumbnails", {}).get("medium", {}).get("url")
                },
                "duration": content_details.get("duration"),
                "channel_name": snippet.get("channelTitle")
            }
            #print(f"Result: {result}")
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return jsonify({"error": str(e)}), 500
        #print("Result:", result)
        return jsonify(result), 200
    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/get-subscription-status', methods=['POST'])
def get_subscription_status():
    data = request.get_json()
    user_email = data.get('email')
    
    if not user_email:
        return jsonify({'error': 'Email is required'}), 400

    # Retrieve the customer based on the email
    customers = stripe.Customer.list(email=user_email, limit=1)

    if customers.data:
        # Customer exists, proceed with subscription check
        customer_id = customers.data[0].id
        print(f"Customer {customer_id} found, checking subscriptions.")
    else:
        # No customer found, create a new one
        print(f"No customer found for {user_email}, creating a new customer.")
        customer = create_customer(user_email)
        return jsonify({
            'status': 'Customer created',
            'tier': 'None',  # No subscription since the customer is new
            'customer_id': customer.id,
        }), 201

    try:
        # Fetch subscription details for the existing customer
        subscriptions = stripe.Subscription.list(customer=customer_id, status='all', limit=1)
     
        if not subscriptions.data:
            # Customer exists but has no active subscriptions
            print("here")
            return jsonify({
                'status': 'Not Active',
                'tier': 'Free',  # No active subscriptions
                'customer_id': customer_id,
            })

        # Get the subscription details and tier information
        print("not here")
        subscription = subscriptions.data[0]
        price_id = subscription['items']['data'][0]['price']['lookup_key']
        subscription_item = subscriptions['data'][0]['items']['data'][0] if subscriptions['data'][0]['items']['data'] else "Free"  # First subscription item or "Free" if empty
        

        return jsonify({
            'customer_id': customer_id,
            'status': 'Subscribed',
            'tier' : subscription_item['price']['nickname'],
            'current_period_end': subscription['current_period_end'],
            'next_billing_date': subscription['current_period_end'],
        })
    except Exception as e:
        print(f"Stripe error: {e}")
        return jsonify({'error': 'Stripe error'}), 500

# Function to create a new Stripe customer
def create_customer(email):
    try:
        customer = stripe.Customer.create(
            email=email,
            description='Created via subscription status check'
        )
       
        return customer
    except Exception as e:
        print(f"Error creating customer: {e}")
        raise Exception('Stripe customer creation failed')






@app.route('/api/transcribe_youtube', methods=['POST'])
def transcribe_youtube():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data sent"}), 400

    link = data.get('youtube_url')
    if not link:
        return jsonify({"error": "URL is required."}), 400

    youtubeRegex = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+"
    match = re.match(youtubeRegex, link)
    
    if match:
        # Attempt to extract the video ID from the URL
        video_id = None
        if "youtu.be" in link:
            video_id = link.split("/")[-1]
            print(video_id)
        else:
            video_id = link.split("v=")[-1].split("&")[0]
            print(video_id)

        try:
            # Attempt to get the transcript for the given video ID
            content = get_transcript_with_rotation(video_id, proxies_list)
       

            content = [
                {
                    key: value
                    for key, value in item.items() if key != "duration"
                }
                    for item in content
                ]

            content = [
                {
                    "text": remove_fillers(item["text"]),
                    "start_time": item["start"]
                }
                for item in content
            ]
        
            return jsonify({"content": content, "length": len(content)}), 200
           # return jsonify({"content": content, "source": "YouTube"}), 200
        except TranscriptsDisabled:
            return jsonify({"error": "Transcripts are disabled for this video."}), 400
        except NoTranscriptFound:
            return jsonify({"error": "No transcript found for this video."}), 404
        except Exception as e:
            # Handle other possible exceptions
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid YouTube URL provided."}), 400

@app.route('/api/user', methods=['POST'])
def store_user():
    user_info = request.get_json()
    print("USERUSER")
    print(user_info)
    try:
        with get_db_connection_context() as conn:
            upsert_user(user_info, conn)
            return jsonify({"message": "User information stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_summary/<string:link_id>', methods=['GET'])
def get_summary(link_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT video_url, video_summary_json FROM youtubelinks WHERE link_id = %s", (link_id,))
            result = cur.fetchone()
        if result:
            return jsonify({
                'video_url': result[0],
                'summary': result[1]
            }), 200
        return jsonify({'message': 'Summary not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        put_db_connection(conn)

@app.route('/api/check_email_by_ip', methods=['POST'])
def api_check_email_by_ip():
    data = request.json
    ip = data.get('ip')
    
    if not ip:
        return jsonify({"error": "IP address is required"}), 400
    
    conn = get_db_connection()
    try:
        has_email = has_email_by_ip(ip, conn)
        return jsonify({"has_email": has_email})
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500
    finally:
        put_db_connection(conn)


@app.route('/api/get_url_count_by_ip', methods=['POST'])
def get_url_count_by_ip():
    data = request.get_json()
    if 'ip' not in data:
        return jsonify({"error": "Missing IP address"}), 400

    try:
        with get_db_connection_context() as conn:
            count = get_url_count_by_ips(data, conn)
            return jsonify({"count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def with_db_connection(f):
    """Decorator to handle database connections"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db_connection()
            return f(*args, **kwargs, conn=conn)
        finally:
            if conn:
                put_db_connection(conn)
    return wrapper

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_transcript_with_retries(video_id, proxies, max_retries=4):
    """Get transcript with multiple retries using proxy"""
    for i in range(max_retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
            return ' '.join([entry['text'] for entry in transcript])
        except Exception as e:
            logger.error(f"Proxy request failed: {str(e)}")
            if i == max_retries - 1:
                raise e
            continue

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_openai_request(prompt, apimodel):
    """Retry wrapper for OpenAI API calls"""
    try:
        return call_openai_api(prompt, apimodel)
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

@app.route('/api/process_video', methods=['POST'])
@with_db_connection
def process_video(conn):
    """Process YouTube video and generate summary"""
    try:
        logger.info("Starting process_video")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data sent"}), 400

        logger.info(f"Received data type: {type(data)}")
        logger.info(f"Data keys: {data.keys()}")

        # Extract and validate required fields
        required_fields = {
            'youtube_url': data.get('youtube_url'),
            'firebase_uid': data.get('firebase_uid'),
            'user_id': data.get('user_id')
        }
        
        logger.info(f"Required fields: {required_fields}")
        
        video_id = data.get('video_id')
        logger.info(f"Extracted video_id: {video_id}")



        # Create link_data dictionary
        link_data = {
            'user_id': required_fields['user_id'],
            'video_url': required_fields['youtube_url']
        }

        # Check if video exists and get processed data
        try:
            print("*******************************HERE")
            exists, response = get_or_process_video_link(link_data, conn)
            print("*******************************HERE")
            print(exists)
            print(response)
            logger.info(f"Video exists in database: {exists}")
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            return jsonify({"error": "Failed to process video link"}), 500

        # Handle existing video case
        if exists:
            try:
                print("<<<<<<<<< Video already exists >>>>>>>>>")
                print(f"Video ID: {video_id}")
                combined_text = get_transcript_with_rotation(video_id, proxies_list)
                chroma_path = generate_data_store(combined_text)
                response.update({"chroma_path": chroma_path})
                print(response)
                return jsonify(response), 200
            except Exception as e:
                logger.error(f"Error processing existing video: {str(e)}")
                return jsonify({"error": "Failed to process existing video"}), 500
        else:
            try:
                #print("Transcribing video...")
                combined_texts = get_transcript_with_rotation(video_id, proxies_list)
                #print("Transcript loading to chromaDB:")
                chroma_path = generate_data_store(combined_texts)
                #print("Transcript loaded to chromaDB")
                prompt_0 = ""
                prompt_1 = ""
                prompt_2 = ""
                prompt_3 = ""
                #print("combined_texts", combined_texts)
                if len(combined_texts) > 900:
                    first_split_index = len(combined_texts) // 3
                    second_split_index = 2 * len(combined_texts) // 3
                    first_part_json = combined_texts[:first_split_index]
                    second_part_json = combined_texts[first_split_index:second_split_index]
                    third_part_json = combined_texts[second_split_index:]

                    combined_text_1 = [{
                        key: value
                        for key, value in item.items() if key != "duration"
                    } for item in first_part_json]

                    combined_text_2 = [{
                        key: value
                        for key, value in item.items() if key != "duration"
                    } for item in second_part_json]

                    combined_text_3 = [{
                        key: value
                        for key, value in item.items() if key != "duration"
                    } for item in third_part_json]

                    combined_text_1 = [{
                        "text": remove_fillers(item["text"]),
                        "start_time": item["start"]
                    } for item in combined_text_1]

                    combined_text_2 = [{
                        "text": remove_fillers(item["text"]),
                        "start_time": item["start"]
                    } for item in combined_text_2]

                    combined_text_3 = [{
                        "text": remove_fillers(item["text"]),
                        "start_time": item["start"]
                    } for item in combined_text_3]

                    prompt_1 = f"""Given the following Transcript: "{combined_text_1}" """
                    prompt_1 = prompt_1 + structured_prompt
                    prompt_2 = f"""Given the following Transcript: "{combined_text_2}" """
                    prompt_2 = prompt_2 + structured_prompt
                    prompt_3 = f"""Given the following Transcript: "{combined_text_3}" """
                    prompt_3 = prompt_3 + structured_prompt
                else:
                    combined_text_0 = [{
                        key: value
                        for key, value in item.items() if key != "duration"
                    } for item in combined_texts]
                    prompt_0 = f"Given the following Transcript: {combined_text_0} " + structured_prompt
                    
            except TranscriptsDisabled:
                return jsonify({"error": "Transcripts are disabled for this video."}), 400
            except NoTranscriptFound:
                return jsonify({"error": "No transcript found for this video."}), 404

        try:
       
       
            answer = process_transcript(combined_texts, data.get('videoTitle'))
            
            logger.info("Building response")
            response = {
                "summary": answer,
                "chroma_path": chroma_path
            }
            print(response)
            increment_url_count(required_fields['user_id'], conn)
            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in transcript processing: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            raise

    except Exception as e:
        logger.error(f"Unexpected error in process_video: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def process_transcript(combined_texts, video_title):
    """Process transcript and generate summary"""
    if len(combined_texts) > 900:
        return process_long_transcript(combined_texts)
    return process_short_transcript(combined_texts, video_title)

def process_long_transcript(combined_texts):
    """Handle long transcripts by splitting and processing in parallel"""
    # Split transcript into thirds
    splits = split_transcript(combined_texts)
    prompts = [create_prompt(split) for split in splits]
    
    # Process prompts in parallel
    responses = call_api_in_parallel(prompts, 'gpt-4o', app)
    if not responses or len(responses) != 3:
        raise Exception("Failed to get complete responses from API calls")
    
    return combine_jsons(*responses)

def process_short_transcript(combined_texts, video_title):
    """Handle short transcripts with single API call"""
    combined_text = [{
        key: value
        for key, value in item.items() if key != "duration"
    } for item in combined_texts]
    
    prompt = f"Given the following Transcript: {combined_text} -----> videoTitle: {video_title} {structured_prompt}"
    
    answer = process_openai_request(prompt, 'gpt-4o')
    if hasattr(answer, 'key_conclusions'):
        answer.summary = answer.key_conclusions
        del answer.key_conclusions
    return answer

def split_transcript(combined_texts):
    """Split transcript into three parts"""
    first_split_index = len(combined_texts) // 3
    second_split_index = 2 * len(combined_texts) // 3
    
    splits = [
        combined_texts[:first_split_index],
        combined_texts[first_split_index:second_split_index],
        combined_texts[second_split_index:]
    ]
    
    return [process_split(split) for split in splits]

def process_split(split):
    """Process individual transcript split"""
    return [{
        "text": remove_fillers(item["text"]),
        "start_time": item["start"]
    } for item in split if "text" in item and "start" in item]

def create_prompt(split):
    """Create prompt for transcript split"""
    return f"""Given the following Transcript: "{split}" """ + structured_prompt

def extract_video_id(youtube_url):
    reg_exp = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.match(reg_exp, youtube_url)
    return match.group(1) if match else None

@app.route('/api/videos', methods=['GET'])
def get_videos():
    try:
        # Get the limit parameter from query string, default to 10 if not provided
        limit = request.args.get('limit', default=20, type=int)
        
        # Get database connection
        conn = get_db_connection()
        try:
            # Get video details
            videos = get_video_details(conn, limit)
            return jsonify(videos), 200
        finally:
            # Always return the connection to the pool
            put_db_connection(conn)
            
    except Exception as e:
        print(f"Error fetching videos: {str(e)}")
        return jsonify({"error": "Failed to fetch videos"}), 500

@app.route('/api/youtube/insert', methods=['POST'])
def insert_youtube_video():
    conn = None  # Initialize conn to None
    try:
        print("\n=== Starting YouTube Video Insert ===")
        data = request.get_json()
       # print(f"Received data: {json.dumps(data, indent=2)}")
        
        # Get required fields
        firebase_uid = data.get('firebase_uid')
        youtube_url = data.get('video_url')
        ip = data.get('ip')
        user_id = data.get('user_id')


        if not youtube_url:
            return jsonify({"error": "YouTube URL is required"}), 400

        # Get database connection and user_id
        conn = get_db_connection()
       

        # Handle video summary
        video_summary = data.get('video_summary_json')
        print(f"video_summary")
        if video_summary:
            video_summary = json.dumps(video_summary) if not isinstance(video_summary, str) else video_summary

        # Create link_data with the correct user_id
        link_data = {
            'user_id': user_id,
            'video_url': youtube_url,
            'video_summary_json': video_summary
        }

        # Add optional fields
        optional_fields = ['title', 'default_thumbnail', 'medium_thumbnail', 
                         'channel_name', 'published_date', 'channel_url', 
                         'video_description']
        for field in optional_fields:
            if field in data:
                link_data[field] = data.get(field)

       # print(f"\nFinal link_data being sent to database: {json.dumps(link_data, indent=2)}")

        success, message = insert_youtube_link(link_data, conn)
        print(f"Insert result - Success: {success}, Message: {message}")
        
        if success:
          #  print(f"incrementing count of user ID: {user_id}")
            #increment_url_count(user_id, conn)  # Increment the URL count
            
            with conn.cursor() as cur:
                cur.execute("SELECT link_id FROM youtubelinks WHERE video_url = %s", 
                          (youtube_url,))
                link_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Video processed and data stored successfully", 
                          "link_id": link_id}), 201
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        print(f"\nError inserting YouTube data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:  # Only try to return the connection if it was successfully acquired
            try:
                put_db_connection(conn)
                print("Database connection returned to pool")
            except Exception as e:
                print(f"Error returning connection to pool: {str(e)}")
            print("Database connection returned to pool")
   

@app.route('/api/get-user-id', methods=['POST'])
def get_user_id():
    print("\n=== Starting get-user-id API call ===")
    
    # Log incoming request data
    data = request.get_json()
    print(f"Received request data: {json.dumps(data, indent=2)}")
    
    firebase_uid = data.get('firebase_uid')
    ip = data.get('ip')
    print(f"Extracted values - firebase_uid: {firebase_uid}, ip: {ip}")

    # Validate input
    if not firebase_uid and not ip:
        print("Error: Missing required parameters")
        return jsonify({"error": "Either firebase_uid or ip is required"}), 400

    print("Getting database connection...")
    conn = get_db_connection()
    try:
        # Determine which lookup method to use
        if firebase_uid == 'anonymous' or not firebase_uid:
            print(f"Looking up user_id by IP: {ip}")
            user_id = get_user_id_by_ip(ip, conn)
        else:
            print(f"Looking up user_id by Firebase UID: {firebase_uid}")
            user_id = get_user_id_by_firebase_uid(firebase_uid, conn)

        print(f"Lookup result - user_id: {user_id}")

        if user_id:
            # Get URL count for the user
            print(f"Getting URL count for user_id: {user_id}")
            url_count = get_url_count_by_id(user_id, conn)
            print(f"URL count retrieved: {url_count}")
            
            print("Successfully found user_id and url_count, returning response")
            return jsonify({
                "user_id": user_id,
                "url_count": url_count
            }), 200
        else:
            print("No user_id found")
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        print(f"Error occurred during processing: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try:
                put_db_connection(conn)
                print("Database connection returned to pool")
            except Exception as e:
                print(f"Error returning connection to pool: {str(e)}")
        print("=== Completed get-user-id API call ===\n")

@contextmanager
def get_db_connection_context():
    """
    Context manager for database connections to ensure proper handling of connections.
    Usage:
        with get_db_connection_context() as conn:
            # use connection
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            put_db_connection(conn)

def make_proxied_request(url, proxies_list):
    """
    Make a request using a rotating proxy list
    """
    logger.info("Starting make_proxied_request")
    logger.info(f"URL: {url}")
    logger.info(f"Proxies list type: {type(proxies_list)}")
    logger.info(f"Proxies list content: {proxies_list}")

    try:
        # Convert single proxy dict to list if needed
        if isinstance(proxies_list, dict):
            proxies = [proxies_list]
            logger.info("Converting single proxy dict to list")
        elif isinstance(proxies_list, str):
            logger.warning(f"Received string instead of proxy dict/list: {proxies_list}")
            # Handle string proxy by converting to proper format
            proxies = [{"http": proxies_list, "https": proxies_list}]
        else:
            proxies = proxies_list
        
        logger.info(f"Processed proxies: {proxies}")

        for proxy in proxies:
            try:
                logger.info(f"Attempting request with proxy: {proxy}")
                response = requests.get(url, proxies=proxy, timeout=10)
                logger.info(f"Proxy request status code: {response.status_code}")
                if response.status_code == 200:
                    return response
            except Exception as e:
                logger.error(f"Proxy request failed: {str(e)}")
                logger.error(f"Proxy that failed: {proxy}")
                continue
        
        # If all proxies fail, try without proxy
        logger.warning("All proxies failed, attempting request without proxy")
        return requests.get(url)
        
    except Exception as e:
        logger.error(f"Request failed completely: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)