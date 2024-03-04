import json
# Assuming pydantic_core.core_schema is correctly installed and used
from flask import Blueprint, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re

# Define the blueprint
youtube_transcriber = Blueprint('youtube_transcriber', __name__)

@youtube_transcriber.route('/transcribe_youtube', methods=['POST'])
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
        else:
            video_id = link.split("v=")[-1].split("&")[0]

        try:
            # Attempt to get the transcript for the given video ID
            content = YouTubeTranscriptApi.get_transcript(video_id)

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
