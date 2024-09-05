import json
from datetime import timedelta
import logging
import os

def format_timestamp(seconds):
    """Formats timestamp into HH:MM:SS without milliseconds."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def process_transcripts(json_file_path, output_file_path):
    log_file_path = os.path.join(os.path.dirname(output_file_path), 'process_log.txt')

    # Initialize logging to the log file
    logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(message)s')
    
    logging.info("Starting transcript processing...")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except IOError as e:
        logging.error(f"Error reading JSON file: {e}")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file: {e}")
        return

    formatted_texts = []
    
    for title, details in data.items():
        link = details.get('link', 'No link available')
        transcript = details.get('transcript', None)
        
        if transcript == "Transcript not available":
            formatted_texts.append(f"Title: {title}")
            formatted_texts.append(f"Link: {link}")
            formatted_texts.append("\nTranscript not available.\n")
            logging.info(f"Processed {title} - Transcript not available.")
            continue

        if transcript == "Transcripts disabled":
            formatted_texts.append(f"Title: {title}")
            formatted_texts.append(f"Link: {link}")
            formatted_texts.append("\nTranscripts disabled.\n")
            logging.info(f"Processed {title} - Transcripts disabled.")
            continue

        if isinstance(transcript, str):
            continue
        
        formatted_texts.append(f"Title: {title}")
        formatted_texts.append(f"Link: {link}\n")
        
        last_time = 0
        current_text = []

        for entry in transcript:
            if not isinstance(entry, dict) or 'start' not in entry or 'text' not in entry:
                formatted_texts.append(f"Unexpected entry format: {entry}")
                logging.error(f"Unexpected entry format for {title}: {entry}")
                continue

            start = entry.get('start', 0)
            text = entry.get('text', '')
            
            start_time = format_timestamp(start)
            
            if start > last_time + 60:
                formatted_texts.append(f"(Start: {format_timestamp(last_time)})")
                formatted_texts.append(" ".join(current_text))
                formatted_texts.append("")
                current_text = []
                last_time = start
            
            current_text.append(text)
        
        if current_text:
            formatted_texts.append(f"(Start: {format_timestamp(last_time)})")
            formatted_texts.append(" ".join(current_text))
            formatted_texts.append("")

        logging.info(f"Processed transcript for {title}.")

    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(formatted_texts))
    except IOError as e:
        logging.error(f"Error writing to output file: {e}")
        return

    logging.info(f"Formatted text has been written to {output_file_path}")
