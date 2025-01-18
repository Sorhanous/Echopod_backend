from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
import shutil
import  logging
import time
import uuid

# Set up # # logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_CHROMA_PARENT_PATH = "chroma"
BASE_CHROMA_PATH = os.path.join(BASE_CHROMA_PARENT_PATH, "chroma")

def generate_data_store(combined_texts=None):
    try:
        cleanup_old_databases()
        if combined_texts is None:
            raise ValueError("No transcript entries provided.")
        logging.info(f"Loaded {len(combined_texts)} transcript entries.")
        
        combined_documents = combine_transcript_entries(combined_texts)
        logging.info(f"Combined into {len(combined_documents)} documents.")
        
        # Log combined documents for verification
        #for i, doc in enumerate(combined_documents):
            #logging.info(f"Combined Document {i}:\n{doc}\n{'-'*60}")
        
        chunks = split_text(combined_documents)
        chroma_path = save_to_chroma(chunks)  # Get the path here
        return chroma_path  # Return the path
    except Exception as e:
        logging.error(f"Error in generate_data_store: {e}")
        return None

def combine_transcript_entries(entries, max_combined_length=1500):
    try:
        combined_entries = []
        current_text = ""
        current_start = entries[0]['start']

        for entry in entries:
            if len(current_text) + len(entry['text']) + 1 > max_combined_length:
                combined_entries.append({"text": current_text.strip(), "start": seconds_to_hms(current_start)})
                current_text = entry['text']
                current_start = entry['start']
            else:
                current_text += " " + entry['text']

        if current_text:
            combined_entries.append({"text": current_text.strip(), "start": seconds_to_hms(current_start)})

        return combined_entries
    except Exception as e:
        logging.error(f"Error in combine_transcript_entries: {e}")
        return []

def seconds_to_hms(seconds):
    try:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"
    except Exception as e:
        logging.error(f"Error in seconds_to_hms: {e}")
        return "00:00:00"

def split_text(documents: list[dict]):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2500,  # Increase chunk size for more context
            chunk_overlap=750,  # Adjust overlap to maintain continuity
            length_function=len,
            add_start_index=True,
        )
        
        chunks = []
        for document_dict in documents:
            document = Document(page_content=document_dict["text"], metadata={
                "start": document_dict["start"]
            })
            document_chunks = text_splitter.split_documents([document])
            
            # Update metadata for each chunk to include the start time of the original document
            for chunk in document_chunks:
                chunk.metadata["original_start"] = document_dict["start"]
            
            chunks.extend(document_chunks)
          #  logging.info(f"Document starting at {document.metadata['start']} split into {len(document_chunks)} chunks.")

        logging.info(f"Split {len(documents)} documents into {len(chunks)} total chunks.")
        return chunks
    except Exception as e:
        logging.error(f"Error in split_text: {e}")
        return []

def save_to_chroma(chunks: list[Document]):
    try:
        if not os.path.exists(BASE_CHROMA_PARENT_PATH):
            os.makedirs(BASE_CHROMA_PARENT_PATH)
        
        unique_chroma_path = os.path.join(BASE_CHROMA_PARENT_PATH, f"chroma_{uuid.uuid4()}")
        #print(unique_chroma_path)
        
        # Clear out the database first if it exists.
        if os.path.exists(unique_chroma_path):
            shutil.rmtree(unique_chroma_path)
       # logging.info(f"Deleted existing database at {unique_chroma_path}.")
        
        # Create a new DB from the documents.
        db = Chroma.from_documents(
            chunks, OpenAIEmbeddings(), persist_directory=unique_chroma_path
        )
        db.persist()
        logging.info(f"Saved {len(chunks)} chunks to {unique_chroma_path}.")
        return unique_chroma_path  # Return the path here
    except Exception as e:
        logging.error(f"Error in save_to_chroma: {e}")
        return None


def cleanup_old_databases(base_path=BASE_CHROMA_PARENT_PATH, age_limit_hours=1):
    """Remove old Chroma databases to free up space."""
    current_time = time.time()
    age_limit_seconds = age_limit_hours * 60 * 60
    logging.info(f"Starting cleanup of old databases in {base_path}.")
    logging.info(f"Current time: {current_time}")
    
    if not os.path.exists(base_path):
        logging.warning(f"Base path {base_path} does not exist.")
        return

    for root, dirs, files in os.walk(base_path):
        logging.info(f"Checking directory: {root}")
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            if os.path.isdir(dir_path):
                creation_time = os.path.getctime(dir_path)
                age_seconds = current_time - creation_time
             #   logging.info(f"Directory {dir_path} age: {age_seconds / 3600:.2f} hours")
                
                if age_seconds > 60:
                    try:
                        shutil.rmtree(dir_path)
                      #  logging.info(f"Deleted old database at {dir_path}")
                    except Exception as e:
                        logging.error(f"Error deleting directory {dir_path}: {e}")

# Call the cleanup_old_databases function to test
cleanup_old_databases()
