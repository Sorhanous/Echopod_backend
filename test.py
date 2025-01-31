import requests
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

proxies = {
    'http': 'http://sp6hfygjve:UnvAe7wcT5Z8n_wv7x@state.smartproxy.com:10000',
    'https': 'http://sp6hfygjve:UnvAe7wcT5Z8n_wv7x@state.smartproxy.com:10000'
    
}


def extract_youtube_transcript_with_proxy(video_url):
    """
    Extract the transcript for a given YouTube video URL using a proxy.
    
    Args:
        video_url (str): The URL of the YouTube video.
        
    Returns:
        dict: A dictionary containing the transcript or an error message.
    """
    # Regular expression to extract video ID from the URL
    video_id_regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/.*v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.match(video_id_regex, video_url)

    if not match:
        return {"error": "Invalid YouTube URL provided."}

    video_id = match.group(1)

    try:
        # Configure the session with proxy
        session = requests.Session()
        session.proxies = proxies
        
        # Fetch the transcript with proxy
        transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
        # Remove duration and clean text
        cleaned_transcript = [
            {"text": item["text"], "start_time": item["start"]}
            for item in transcript
        ]
        
        return {"transcript": cleaned_transcript}

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video."}
    
    except NoTranscriptFound:
        return {"error": "No transcript found for this video."}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example usage
if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=SpuXqNakP2A"
    result = extract_youtube_transcript_with_proxy(video_url)
    
    if "transcript" in result:
        print("Transcript extracted successfully:")
        for item in result["transcript"][:5]:  # Print first 5 transcript items
            print(f"{item['start_time']}: {item['text']}")
    else:
        print(f"Error: {result['error']}")
