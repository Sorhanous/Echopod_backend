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
from functions import combine_jsons
from concurrent.futures import ThreadPoolExecutor, as_completed






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




def call_api_in_parallel(prompts, apimodel, app):
  responses = []
  with ThreadPoolExecutor(max_workers=4) as executor:
      future_to_prompt = {executor.submit(call_openai_api_with_context, prompt, apimodel, app): prompt for prompt in prompts}
      for future in as_completed(future_to_prompt):
          try:
              response = future.result()  # Assume this now returns a dict
              responses.append(response)
          except Exception as exc:
              print(f"API call generated an exception: {exc}")
  return responses  # Make sure this is defined and returned correctly

def call_openai_api_with_context(prompt, apimodel, app):
  with app.app_context():
      # Your existing call_openai_api logic here, assuming it returns a dict or list
      return call_openai_api(prompt, apimodel)




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
                                                      "role": "system",
                                                      "content": structured_prompt
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
      combined_texts = YouTubeTranscriptApi.get_transcript(video_id)
    
      prompt_0 = ""
      prompt_1 = ""
      prompt_2 = ""
      prompt_3 = ""
    
      if len(combined_texts) > 900:
          # Calculate splitting indices for three equal parts
          first_split_index = len(combined_texts) // 3
          second_split_index = 2 * len(combined_texts) // 3
    
          # Split the JSON data into three parts
          first_part_json = combined_texts[:first_split_index]
          second_part_json = combined_texts[first_split_index:second_split_index]
          third_part_json = combined_texts[second_split_index:]
          print(len(combined_texts))
          # Keep as the same type, just remove "duration"
          combined_text_1 = [{key: value for key, value in item.items() if key != "duration"} for item in first_part_json]
          print(len(combined_text_1))
          combined_text_2 = [{key: value for key, value in item.items() if key != "duration"} for item in second_part_json]
          print(len(combined_text_2))
          combined_text_3 = [{key: value for key, value in item.items() if key != "duration"} for item in third_part_json]
          print(len(combined_text_3))

       # f"""Given the folloing Transcript: "{combined_text}" """
          # Convert list of dictionaries to string representation right before using in the prompt
          prompt_1 = f"""Given the following Transcript: "{combined_text_1}" """ 
          prompt_1 = prompt_1 + structured_prompt 
          prompt_2 = f"""Given the following Transcript: "{combined_text_2}" """ 
          prompt_2 = prompt_2 + structured_prompt 
          prompt_3 = f"""Given the following Transcript: "{combined_text_3}" """ 
          prompt_3 = prompt_3 + structured_prompt 
      else:
          # If less than 900, process as a whole and remove "duration"
          combined_text_0 = [{key: value for key, value in item.items() if key != "duration"} for item in combined_texts]
    
          # Convert list of dictionaries to string representation right before using in the prompt
          prompt_0 = f"Given the following Transcript: {combined_text_0} " + structured_prompt
    
  except TranscriptsDisabled:
      return jsonify({"error": "Transcripts are disabled for this video."}), 400
  except NoTranscriptFound:
      return jsonify({"error": "No transcript found for this video."}), 404


  
  #determine which model to use:
  if len(combined_texts) > 320:
    apimodel = Model4
  else:
    apimodel = Model3
  answer = {}
 

# Check if the entire transcript was short enough to not require splitting
  if len(prompt_0) > 0:
      answer = call_openai_api(prompt_0, apimodel)
  else:
      # Assuming prompts are split, prepare them for parallel processing
      prompts = [prompt_1, prompt_2, prompt_3]
      responses = call_api_in_parallel(prompts, apimodel, app)  # Pass app here
  
      # Check if responses are successfully received from all parallel API calls
      if responses and len(responses) == 3:
          answer_1, answer_2, answer_3 = responses
          answer = combine_jsons(answer_1, answer_2, answer_3)  # Assume combine_jsons can handle three inputs
      else:
          answer = {"error": "Failed to get responses from API calls."}
  return answer



def extract_video_id(youtube_url):
  reg_exp = r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*'
  match = re.match(reg_exp, youtube_url)
  return match.group(7) if match and len(match.group(7)) == 11 else None


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)








