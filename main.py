from flask import Flask, jsonify, request
import json
from flask_cors import CORS
from pydantic_core.core_schema import dataclass_schema
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import os  
import openai
import re 
#import requests
#from bs4 import BeautifulSoup



OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)



def split_text(text, max_length=25000):
  """
  Splits the text into chunks with a maximum length of max_length.
  This function ensures that chunks are split on sentence boundaries when possible.
  """
  sentences = text.split('. ')
  current_chunk = ""
  chunks = []
  for sentence in sentences:
      if len(current_chunk) + len(sentence) < max_length:
          current_chunk += sentence + '. '
      else:
          chunks.append(current_chunk)
          current_chunk = sentence + '. '
  if current_chunk:
      chunks.append(current_chunk)
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
      merged_response["sentiment_analysis"] += response["sentiment_analysis"] + " "
      merged_response["reliability_score"] += response["reliability_score"] + " "
      merged_response["political_leaning"] += response["political_leaning"] + " "

  return merged_response


@app.route('/')
def health_check():
    return 'I am Healthy :)'


@app.route('/transcribe_youtube', methods=['POST'])
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
            content = YouTubeTranscriptApi.get_transcript(video_id)
            #content = ' '.join([item['text'] for item in transcript_list])


            #print(content)
            # Concatenate all text items in the transcript list
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
      except TranscriptsDisabled:
          return jsonify({"error": "Transcripts are disabled for this video."}), 400
      except NoTranscriptFound:
          return jsonify({"error": "No transcript found for this video."}), 404
      #chunks = split_text(combined_text)
      #print(len(chunks))
      
      structured_prompt = f"""To ensure all projects are captured and listed in the actionable advice section, you must consider  the need for a comprehensive and exhaustive list of all mentioned projects, services, or products within each category, emphasizing the importance of not missing any mentions.

Analyze the following transcript which is in json format:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "You absolute piece of."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Yes, I'm gonna give you exactly what"
      }}
      ]
  }}

 and read all the text from all the arrays to get the transcript and generate a structured response in JSON format covering the following points. Ensure you provide a comprehensive and exhaustive list of all projects, services, or products mentioned, categorized by their respective topics (e.g., gaming, gambling, AI). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details for each category. My decision-making relies on this information being accurate and all-encompassing. Please format the actionable advice as an array under each category, ensuring no project or mention is overlooked. also include the "start" time stamp you see for each item and include them in the json format shown below.
It doesnt alwasy have to be actionable advice, but all that is mentioned will go under that category in the json shown below.

Provide a concise summary of the key points discussed.
Detail all actionable advice given, categorized by topic. Include each piece of advice or mention of projects, services, etc., under the corresponding category. It's vital that all advice or mentions are captured.
Analyze the overall sentiment of the transcript.
Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies.
Describe the political leaning of the message, if applicable.
Transcript: "{combined_text}"

Please format your response as follows - make sure each item has its own line and not grouped even if they share the same explaination:

{{
  "summary": "Here is a brief summary...",
  "actionable_advice": {{
    "<category 1>": [
      "1. one of the items in the list of advice or projects in category 1...each line will have one item mentioned followed by the next line for the next items. After the item name: explaination mentioned in the transcript"
      1.1. <start time of the item>
      "2. Another piece of advice or project mention...After the item name: explaination mentioned in the transcript",
      2.2 <start time of the item>
      ...
    ],
    "<category 2>": [
      "1. one of the items in the Comprehensive list of advice or projects in category 2...After the item name: explaination mentioned in the transcript",
      1.1. <start time of the item>
      "2. Another piece of advice or project mention...After the item name: explaination mentioned in the transcript",
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
              model="gpt-4-turbo-preview",
              messages=[
                  {
                      "role": "system",
                      "content": structured_prompt
                  }
              ]
          )

          response_content = completion.choices[0].message.content
          if response_content:
              # Directly parse and return the JSON content
              response_dict = json.loads(response_content)  # This parses the JSON string into a Python dict
              print(response_dict)
              return jsonify(response_dict)  # Use the parsed dict here
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
