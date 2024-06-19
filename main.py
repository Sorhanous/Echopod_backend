from flask import Flask, jsonify, request
import json
from flask_cors import CORS
from pydantic_core.core_schema import dataclass_schema
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import os
import openai
import re
from google.cloud import secretmanager
from dotenv import load_dotenv
from prompts import structured_prompt
from transcribe import youtube_transcriber
from functions import combine_jsons
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.discovery import build
from database import get_db_connection, put_db_connection, upsert_user, store_youtube_link_data, get_or_process_video_link, get_user_id_by_firebase_uid
from config import secrets  # Import secrets from config
from create_database import generate_data_store
import shutil
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate




CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based on the following Video content. 
This is a transcript from a YouTube video. 
If what the query is looking for doesn't exist, answer based on your knowledge of the topic
If the question is seciically from you the AI, answer based on the context of the conversation and your knowledge of the topic. You must distinguish between
the two types of questions: is it from the video? or just a question from you yourself? rememebr you are a trained model with a knowledge base utside of the video which is useful. 

{context}

---

Question: {question}

"""

def generate_data_store(content: str):
    try:
        # Convert content to Document
        document = Document(page_content=content)
        chunks = split_text([document])
        print('Chunks:', chunks)
        save_to_chroma(chunks)
    except Exception as e:
        print('Error in generate_data_store:', e)

def split_text(documents: list[Document]):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split content into {len(chunks)} chunks.")
        
        # Print the first chunk as an example
        document = chunks[0]
        print(document.page_content)
        print(document.metadata)
        
        return chunks
    except Exception as e:
        print('Error in split_text:', e)
        return []

def save_to_chroma(chunks: list[Document]):
    try:
        # Clear out the database first.
        if os.path.exists(CHROMA_PATH):
            print(f"Clearing existing database at {CHROMA_PATH}")
            shutil.rmtree(CHROMA_PATH)

        # Create a new DB from the documents.
        db = Chroma.from_documents(
            chunks, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
        )
        db.persist()
        print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
    except Exception as e:
        print('Error in save_to_chroma:', e)
        raise


def access_secret_version(secret_id, version_id="latest"):
    """
    Access a secret version in Secret Manager.

    Args:
    project_id: Google Cloud project ID
    secret_id: ID of the secret to access
    version_id: version of the secret (default to "latest")

    Returns:,,,,,,,,,,,,,,,,,,
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
def call_openai_api(_prompt, apimodel):
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
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            content = ' '.join([item['text'] for item in transcript_list])

            generate_data_store(transcript_list)
            
            return jsonify({"content": content}), 200
        except TranscriptsDisabled:
            return jsonify({"error": "Transcripts are disabled for this video."}), 400
        except NoTranscriptFound:
            return jsonify({"error": "No transcript found for this video."}), 404
        except Exception as e:
            # Handle other possible exceptions
            print('Error in transcribe_youtube:', e)
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid YouTube URL provided."}), 400
@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data sent"}), 400

    conversation = data.get('conversation', [])
    query_text = data.get('query')
    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    try:
        embedding_function = OpenAIEmbeddings()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

        results = db.similarity_search_with_relevance_scores(query_text, k=3)
        
        # Log results to check structure
        print(f"Results: {results}")
        
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        
        # Format the prompt with conversation history
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
        prompt = f"{conversation_history}\n\n{PROMPT_TEMPLATE.format(context=context_text, question=query_text)}"

        model = ChatOpenAI(model_name="gpt-4")  # Ensure GPT-4 is used
        response_text = model.predict(prompt)

        # Ensure proper handling of quotes in the response
        clean_response = response_text.replace('\\"', '"').replace("\\'", "'")

        return jsonify({"response": clean_response}), 200
    except Exception as e:
        print('Error in query:', e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/transcribe_youtubes', methods=['POST'])
def transcribe_youtubes():
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
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            content = ' '.join([item['text'] for item in transcript_list])

            generate_data_store(content)
            
            #Concatenate all text items in the transcript list
            #content = ' '.join([item['text'] for item in transcript_list])
            
            return jsonify({"content": content, "source": "YouTube"}), 200
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
    if not firebase_uid:
        return jsonify({"error": "Firebase UID is required."}), 400
    if not youtube_url:
        return jsonify({"error": "YouTube URL is required."}), 400

    if not firebase_uid or not youtube_url:
        return jsonify({"error": "Missing required information."}), 400
    conn = get_db_connection()
    try:
        user_id = get_user_id_by_firebase_uid(firebase_uid, conn)
        link_data = {
            'user_id': user_id,
            'video_url': youtube_url,
        }

        exists, response = get_or_process_video_link(link_data, conn)
        if exists:
            return jsonify(response), 200
        else:
            try:
                print("Transcribing video...")
                combined_texts = YouTubeTranscriptApi.get_transcript(video_id)

                prompt_0 = ""
                prompt_1 = ""
                prompt_2 = ""
                prompt_3 = ""

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
            else:
                prompts = [prompt_1, prompt_2, prompt_3]
                responses = call_api_in_parallel(prompts, apimodel, app)

                if responses and len(responses) == 3:
                    answer_1, answer_2, answer_3 = responses
                    answer = combine_jsons(answer_1, answer_2, answer_3)
                else:
                    answer = {"error": "Failed to get responses from API calls."}

        _, db_status = store_youtube_link_data(
            firebase_uid, youtube_url,
            json.dumps(answer) if not isinstance(answer, str) else answer)

        if db_status != 200:
            print("Error storing YouTube link data:", db_status)
    finally:
        put_db_connection(conn)
    #print(answer)
    return answer

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
