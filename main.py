from flask import Flask, jsonify, request
import json
from flask_cors import CORS
from pydantic_core.core_schema import dataclass_schema
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import os
import openai
import re
from prompts import structured_prompt
from transcribe import youtube_transcriber


#import requests
#from bs4 import BeautifulSoup

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
Model3=os.environ['Model3']
Model4 =os.environ['Model4']
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.register_blueprint(youtube_transcriber)
CORS(app)


def split_text_with_overlap(text, max_length=25000, overlap=150):
    """
    Splits the text into chunks with a maximum length of max_length, including an overlap between chunks.
    
    Parameters:
    - text (str): The input text to split.
    - max_length (int): The maximum length of each chunk.
    - overlap (int): The number of characters to overlap between consecutive chunks.
    
    Returns:
    - List[str]: A list of text chunks with specified overlap.
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



def merge_responses(responses):
  """
  Merges multiple response objects into a single response object.
  """
  merged_response = {
      "summary": "",
      "actionable_advice": {},
      "sentiment_analysis": "",
      "reliability_score": "",
      "political_leaning": ""
  }

  for response in responses:
    merged_response["summary"] += response["summary"] + " "
    for category, advice_list in response["actionable_advice"].items():
      if category not in merged_response["actionable_advice"]:
        merged_response["actionable_advice"][category] = []
      merged_response["actionable_advice"][category].extend(advice_list)
    # For simplicity, we concatenate sentiment, reliability, and leaning.
    # This logic may need refinement based on your specific requirements.
    merged_response[
        "sentiment_analysis"] += response["sentiment_analysis"] + " "
    merged_response["reliability_score"] += response["reliability_score"] + " "
    merged_response["political_leaning"] += response["political_leaning"] + " "

  return merged_response

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
    response_content = response_contents.replace("```json", "").replace("```", "")

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
    combined_text = YouTubeTranscriptApi.get_transcript(video_id)
    #combined_text = ' '.join([item['text'] for item in transcript_list])
    print(len(combined_text))
  except TranscriptsDisabled:
    return jsonify({"error": "Transcripts are disabled for this video."}), 400
  except NoTranscriptFound:
    return jsonify({"error": "No transcript found for this video."}), 404
  #chunks = split_text(combined_text)
  #print(len(chunks))

  combined_texts = f"""Given the folloing Transcript: "{combined_text}" """
  prompt = structured_prompt + combined_texts

  if len(combined_text) > 320:
    apimodel = Model4
  else:
    apimodel = Model3
  answer = call_openai_api(prompt, apimodel)
  return answer


def extract_video_id(youtube_url):
  reg_exp = r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*'
  match = re.match(reg_exp, youtube_url)
  return match.group(7) if match and len(match.group(7)) == 11 else None


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
