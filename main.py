from flask import Flask, jsonify, request
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
from database import get_db_connection, has_email_by_ip, put_db_connection, increment_url_count, get_url_count_by_id, get_url_count_by_ips,  get_user_id_by_ip, upsert_user, store_youtube_link_data, get_or_process_video_link, get_user_id_by_firebase_uid
from config import secrets  
from query_data import query_data





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
OPENAI_API_KEY = secrets['OPENAI_API_KEY']
OPENAI_API_SECRET_2 = secrets['OPENAI_API_SECRET_2']
Model3 = secrets['Model3']
Model4 = secrets['Model4']
Youtube_API_KEY = secrets['Youtube_API_KEY']


proxies_list = [
    
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10001',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10001'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10002',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10002'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10003',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10003'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10004',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10004'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10005',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10005'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10006',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10006'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10007',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10007'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10008',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10008'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10009',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10009'
    },
    {
        'http': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10010',
        'https': 'http://user-sp6hfygjve-country-us-zip-80817:UnvAe7wcT5Z8n_wv7x@us.smartproxy.com:10010'
    }
]


def get_transcript_with_rotation(video_id, proxies_list):
    for proxy in proxies_list:
        try:
            #print(f"Trying proxy: {proxy['http']}")
            # Attempt to get the transcript using the proxy
            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxy)
            #print("Transcript retrieved successfully")
            return transcript
        except Exception as e:
            print(f"Failed with proxy {proxy['http']}, error: {e}")
            # Continue to the next proxy in the list
            continue
    raise Exception("All proxies failed.")

max_chunk_length = 25000
client = openai.OpenAI(api_key=OPENAI_API_KEY)
client_2 = openai.OpenAI(api_key=OPENAI_API_SECRET_2)
app = Flask(__name__)
app.register_blueprint(youtube_transcriber)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
    response = query_data(query_text, video_id, conversation, chroma_path, client, yt_transcript)  # Pass query_text, video_id, conversation, and chroma_path to the query_data function
    return jsonify(response)

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
            #content = ' '.join([item['text'] for item in transcript_list])
            #print("#############################")
           # print(content)

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
            print("#############################")
            # Concatenate all text items in the transcript list
            #content = ' '.join([item['text'] for item in transcript_list])
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
    conn = get_db_connection()
    try:
        upsert_user(user_info, conn)
        response_message = {"message": "User information stored successfully"}
        status_code = 200
    except Exception as e:
        response_message = {"error": str(e)}
        status_code = 500
    finally:
        put_db_connection(conn)
    return jsonify(response_message), status_code

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

    ip = data['ip']
    #print("HELLOL " , data)
    conn = get_db_connection()
    try:
        count = get_url_count_by_ips(data, conn)  # Assuming this function exists and works as intended
        return jsonify({"count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        put_db_connection(conn)



@app.route('/api/get_channel_id', methods=['POST'])
def get_channel_id():
    data = request.get_json()
    if 'video_id' not in data:
        return jsonify({"error": "Missing video ID"}), 400

    video_id = data['video_id']
    api_key = Youtube_API_KEY
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        response = youtube.videos().list(part='snippet', id=video_id).execute()
        channel_id = response['items'][0]['snippet']['channelId']
        return jsonify({"channel_id": channel_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_video', methods=['POST'])
def process_video():
    answer = ''
    data = request.get_json()
    #print('Data', data)
    if not data:
        return jsonify({"error": "No data sent"}), 400

    youtube_url = data.get('youtube_url')
    if not youtube_url:
        return jsonify({"error": "YouTube URL is required."}), 400

    video_id = extract_video_id(youtube_url)
    #print(video_id)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL."}), 400
    firebase_uid = data.get('firebase_uid')
    youtube_url = data.get('youtube_url')
    ip = data.get('ip')
    #print("IP", ip)
    if not firebase_uid:
        return jsonify({"error": "Firebase UID is required."}), 400
    if not youtube_url:
        return jsonify({"error": "YouTube URL is required."}), 400

    if not firebase_uid or not youtube_url:
        return jsonify({"error": "Missing required information."}), 400
    conn = get_db_connection()
  
    count = None
    try:
        #print("ip", firebase_uid)
        if firebase_uid == 'anonymous':
            user_id = get_user_id_by_ip(ip, conn)
            count = get_url_count_by_id(user_id,conn)
        else: 
            user_id = get_user_id_by_firebase_uid(firebase_uid, conn)
            count = get_url_count_by_id(user_id,conn)
        link_data = {
            'user_id': user_id,
            'video_url': youtube_url,
        }
        
        #print("user_id is", user_id)
        exists, response = get_or_process_video_link(link_data, conn)

        #print("exists", exists)
        if exists:
            try:
                #print("Transcribing video...")
                combined_text = get_transcript_with_rotation(video_id, proxies_list)
            except Exception as e:
                #print("Error transcribing video:", e)
                return jsonify({"error": "Failed to transcribe video."}), 500
            #print("Transcript loading to chromaDB:")
            chroma_path = generate_data_store(combined_text)
            response.update({"chroma_path": chroma_path}) 
            response.update({"url_count": count})
            #print(response)
            return jsonify(response), 200
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


            #print(combined_texts)
            if len(combined_texts) > 320:
                apimodel = 'gpt-4o'
            else:
                apimodel = 'gpt-4o'
            answer = {}

            if len(prompt_0) > 0:
                answer = call_openai_api(prompt_0, apimodel)
                    
                if hasattr(answer, 'key_conclusions'):
                    # Rename 'key_conclusions' to 'summary'
                    answer.summary = answer.key_conclusions
                    del answer.key_conclusions

            else:
                prompts = [prompt_1, prompt_2, prompt_3]
                responses = call_api_in_parallel(prompts, apimodel, app)

                if responses and len(responses) == 3:
                    answer_1, answer_2, answer_3 = responses
                    answer = combine_jsons(answer_1, answer_2, answer_3)
                else:
                    answer = {"error": "Failed to get responses from API calls."}

        response, db_status = store_youtube_link_data(
            user_id, youtube_url,
            json.dumps(answer) if not isinstance(answer, str) else answer
        )

        if db_status != 200:
            print("Error storing YouTube link data:", db_status)
            return jsonify(response), db_status
        #print("incrementing count of : ", user_id)
        increment_url_count(user_id, conn)
        response.update({"summary": answer})
        response.update({"url_count": count})
        response.update({"chroma_path": chroma_path}) 
        #print(response)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        put_db_connection(conn) 
    

def extract_video_id(youtube_url):
    reg_exp = r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*'
    match = re.match(reg_exp, youtube_url)
    return match.group(7) if match and len(match.group(7)) == 11 else None

@app.route('/api/get_channel_url', methods=['POST'])
def get_channel_url():
    data = request.get_json()
    if 'video_id' not in data:
        return jsonify({"error": "Missing video ID"}), 400

    video_id = data['video_id']
    api_key = Youtube_API_KEY
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        response = youtube.videos().list(part='snippet', id=video_id).execute()
        channel_id = response['items'][0]['snippet']['channelId']
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        return jsonify({"channel_id": channel_id, "channel_url": channel_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)