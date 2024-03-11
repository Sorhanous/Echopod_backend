from flask import Flask, jsonify, request
import json
from flask_cors import CORS
from pydantic_core.core_schema import dataclass_schema
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import os
import openai
import re
from prompts import structured_prompt, merge_prompt
from transcribe import youtube_transcriber
import concurrent.futures # for parallel calls



#import requests
#from bs4 import BeautifulSoup
#two APi's ready to go:
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
OPENAI_API_SECRET_2 = os.environ['OPENAI_API_SECRET_2']
max_chunk_length=25000

#two models ready to go: 
Model3=os.environ['Model3']
Model4 =os.environ['Model4']
client = openai.OpenAI(api_key=OPENAI_API_KEY)
client_2 = openai.OpenAI(api_key=OPENAI_API_SECRET_2)
app = Flask(__name__)
app.register_blueprint(youtube_transcriber)
CORS(app)




def split_text_with_overlap(text, max_length=25000, overlap=150):
    """
    Splits the text into chunks with a maximum length of max_length, including an overlap between chunks.
"""    
  
    chunks = []
    current_start = 0

    while current_start < len(text):
        # If we are not at the start, move back 'overlap' characters to include some context from the previous chunk
        if current_start > 0:
            start_index = max(0, current_start - overlap)
        else:
            start_index = current_start
        
        end_index = min(len(text), current_start + max_length)
        chunks.append(text[start_index:end_index])
        
        current_start += max_length
    
    return chunks



#initial call:
def call_openai_api(structured_prompt, apimodel):

  try:
    completion = client.chat.completions.create(model=apimodel,
                                                temperature=1,
                                                messages=[{
                                                    "role":
                                                    "system",
                                                    "content":
                                                    structured_prompt
                                                }])

    response_contents = completion.choices[0].message.content
    if response_contents:
      response_content = response_contents.replace("```json", "").replace("```", "")
    else:
      # Raise an exception if response_contents is None or not as expected
      raise ValueError("response_contents is None or not in the expected format.")

    print(response_content)
    if response_content:
      # Directly parse and return the JSON content
      response_dict = json.loads(
          response_content)  # This parses the JSON string into a Python dict
      print(response_dict)
      return jsonify(response_dict)  # Use the parsed dict here
    else:
      return jsonify({"error": "Response content is empty."}), 500

  except Exception as e:
    return jsonify({"error": str(e)}), 500

def merge_chunks(structured_prompt, apimodel):
  try:
    completion = client.chat.completions.create(model=apimodel,
                                                temperature=1,
                                                messages=[{
                                                    "role":
                                                    "system",
                                                    "content":
                                                    structured_prompt
                                                }])
  
    response_contents = completion.choices[0].message.content
    if response_contents:
      response_content = response_contents.replace("```json", "").replace("```", "")
    else:
      # Raise an exception if response_contents is None or not as expected
      raise ValueError("response_contents is None or not in the expected format.")
  
    print(response_content)
    if response_content:
      # Directly parse and return the JSON content
      response_dict = json.loads(
          response_content)  # This parses the JSON string into a Python dict
      print(response_dict)
      return jsonify(response_dict)  # Use the parsed dict here
    else:
      return jsonify({"error": "Response content is empty."}), 500
  
  except Exception as e:
    return jsonify({"error": str(e)}), 500



@app.route('/')
def health_check():
  return 'I am Healthy :)'

@app.route('/process_video', methods=['POST'])
def process_video():
  answer =''
  # Use request.get_json() to correctly parse the JSON payload
  data = request.get_json()
  print(data)
  if not data:
    return jsonify({"error": "No data sent"}), 400

  youtube_url = data.get('youtube_url')
  if not youtube_url:
    return jsonify({"error": "YouTube URL is required."}), 400

  # Extract the YouTube video ID from the URL
  video_id = extract_video_id(youtube_url)
  if not video_id:
    return jsonify({"error": "Invalid YouTube URL."}), 400

  try:
    # Get the transcript for the video
    combined_text = YouTubeTranscriptApi.get_transcript(video_id)
    #combined_text = ' '.join([item['text'] for item in transcript_list])
    print(combined_text)
    print(len(combined_text))
  except TranscriptsDisabled:
    return jsonify({"error": "Transcripts are disabled for this video."}), 400
  except NoTranscriptFound:
    return jsonify({"error": "No transcript found for this video."}), 404
  #chunks = split_text(combined_text)
  #print(len(chunks))
  #create the prompt for initial call
  combined_texts = f"""Given the following Transcript: "{combined_text}" """
  prompt = structured_prompt + combined_texts
  
  #determine which model to use:
  if len(combined_text) > 320:
    apimodel = Model4
  else:
    apimodel = Model3

  
  if(len(combined_text) > max_chunk_length):
    chunks = split_text_with_overlap(combined_text, max_chunk_length)
    print(f"Total chunks: {len(chunks)}")

    # Determine which model to use based on the length of combined_text
    # Example model selection logic, adjust as needed
    #apimodel = "Model4" if len(combined_text) > 320 else "Model3"
    
    responses = []

    # Use ThreadPoolExecutor to call the API in parallel for each chunk
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Prepare future calls, iterating over chunks this time
        future_to_chunk = {executor.submit(call_openai_api, chunk, apimodel): chunk for chunk in chunks}

        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                response = future.result()
                responses.append(response)
            except Exception as exc:
                print(f'Chunk "{chunk}" generated an exception: {exc}')

    # At this point, `responses` contains the API call results for each chunk
    print("responses: ")
    print(responses)
    responses_str = "\n".join(responses)

    # Concatenate the combined responses with the merge_prompt.
    # If you need a different format (e.g., JSON), adjust the concatenation logic accordingly.
    full_prompt = f"{responses_str}\n{merge_prompt}"

    # Now, `full_prompt` contains all responses followed by your merge prompt.
    print("full_prompt: ")
    print(full_prompt)
    
    answer = merge_chunks(full_prompt, apimodel)
    
  else: 
    answer = call_openai_api(prompt, apimodel)

  return answer


def extract_video_id(youtube_url):
  reg_exp = r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*'
  match = re.match(reg_exp, youtube_url)
  return match.group(7) if match and len(match.group(7)) == 11 else None


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)








