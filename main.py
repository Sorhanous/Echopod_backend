from flask import Flask, jsonify, request
import json
from flask_cors import CORS
from pydantic_core.core_schema import dataclass_schema
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import os
import openai
import re  # Import regular expressions
import requests
from bs4 import BeautifulSoup

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return 'I am Healthy :)'

@app.route('/process_video', methods=['POST'])
def process_video():

  if not link:
    raise BadRequestError("Link must be provided")

  youtubeRegex = r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})$"
  # Use request.get_json() to correctly parse the JSON payload
  data = request.get_json()
  # print(data)
  if not data:
      return jsonify({"error": "No data sent"}), 400
    
  try:

    match = re.match(youtubeRegex, link)
    if match:  # If it's a YouTube link

  
      youtube_url = data.get('youtube_url')
      if not youtube_url:
          return jsonify({"error": "YouTube URL is required."}), 400
  
      # Extract the YouTube video ID from the URL
      video_id = extract_video_id(youtube_url)
      if not video_id:
          return jsonify({"error": "Invalid YouTube URL."}), 400
  
      try:
          transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
          content = ' '.join([item['text'] for item in transcript_list])
      except TranscriptsDisabled:
          return jsonify({"error": "Transcripts are disabled for this video."}), 400
      except NoTranscriptFound:
          return jsonify({"error": "No transcript found for this video."}), 404
    else:
      resp = requests.get(link)
      soup = BeautifulSoup(resp.text, 'html.parser')
      title = soup.title.text if soup.title else "No Title Found"
      paragraphs = soup.find_all('p')
      content = "\n".join([paragraph.text for paragraph in paragraphs])
  


    structured_prompt = f"""
    Analyze the following transcript and generate a structured response in JSON format covering the following points. Make sure you understand the json format I am asking you to return as shown below. This API should always return the same format. 
    1. A concise summary of key points discussed.
    2. Any and all actionable advice given, categorized by topic (e.g., gaming, gambling, AI). List each advice with a number under the corresponding category. Don't skip anything, make sure you mention all the advice or mentions of products, services, etc in each category and don't skip anything. for example: if they are talking about crypto, grab all the coins mentioned in the video and put them under their corresponding category. In the entire transcript, grab all the services or products per each category and send it back to me. I can read it myself but i am in a rush and you are faster. my life depends on this returning everything. Make sure actionableAdvice is an array as shown below.
    3. The overall sentiment of the transcript
    4. The reliability of the all the given advice in the transcript based on your knowledge. If there are lies and misinformation, mention it also. 
    5. The political leaning of the message (left-leaning, right-leaning, neutral, other).
  
    Transcript: "{content}"
  
    Please format your response as follows:
    {{
      "summary": "Here is a brief summary...",
      "actionable_advice": {{
        "gaming": [
          "1. Actionable gaming advice 1...",
          "2. Actionable gaming advice 2...",
          ...
        ],
        "gambling": [
          "1. Actionable gambling advice 1...",
          "2. Actionable gambling advice 2...",
          ...
        ],
        "AI": [
          "1. Actionable AI advice 1...",
          "2. Actionable AI advice 2...",
          ...
        ],
        ...
      }},
      "sentiment_analysis": "The overall sentiment is...",
      "reliability_score": "The reliability of the advice is...",
      "political_leaning": "The political leaning is..."
    }}
    """
  



    try:
      completion = client.chat.completions.create(
          model="gpt-4.0",
          messages=[
              {
                  "role": "system",
                  "content": structured_prompt
              }
          ]
      )
  
      # Assuming completion.choices[0].message.content is a JSON string
      response_content = completion.choices[0].message.content
      if response_content:
          response_dict = json.loads(response_content)
          return jsonify(response_dict)
      else:
          return jsonify({"error": "Response content is empty."}), 500
  
    except Exception as e:
      return jsonify({"error": str(e)}), 500


def extract_video_id(youtube_url):
    reg_exp = r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*'
    match = re.match(reg_exp, youtube_url)
    return match.group(7) if match and len(match.group(7)) == 11 else None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
