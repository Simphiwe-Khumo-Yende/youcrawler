import json
from datetime import timedelta
import logging

def format_timestamp(seconds):
    """Formats timestamp into HH:MM:SS without milliseconds."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def process_transcripts(json_file_path, output_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    formatted_texts = []
    
    for title, details in data.items():
        link = details.get('link', 'No link available')
        transcript = details.get('transcript', None)
        
        if transcript == "Transcript not available":
            formatted_texts.append(f"Title: {title}")
            formatted_texts.append(f"Link: {link}")
            formatted_texts.append("\nTranscript not available.\n")
            continue
        
        if isinstance(transcript, str):
            # formatted_texts.append(f"Title: {title}")
            # formatted_texts.append(f"Link: {link}")
            # formatted_texts.append(f"\nInvalid transcript data format. Reason? Transcripts disabled, Transcrpit not availab\n")
            continue
        
        # Debug print
        # print(f"Processing transcript for {title}: {transcript}")
        
        formatted_texts.append(f"Title: {title}")
        formatted_texts.append(f"Link: {link}\n")
        
        # Process the transcript
        last_time = 0
        current_text = []

        for entry in transcript:
            if not isinstance(entry, dict) or 'start' not in entry or 'text' not in entry:
                formatted_texts.append(f"Unexpected entry format: {entry}")
                continue

            start = entry.get('start', 0)
            text = entry.get('text', '')
            
            start_time = format_timestamp(start)
            
            # Check if we need to start a new time interval
            if start > last_time + 60:
                formatted_texts.append(f"(Start: {format_timestamp(last_time)})")
                formatted_texts.append(" ".join(current_text))
                formatted_texts.append("")
                current_text = []
                last_time = start
            
            current_text.append(text)
        
        # Append the remaining text
        if current_text:
            formatted_texts.append(f"(Start: {format_timestamp(last_time)})")
            formatted_texts.append(" ".join(current_text))
            formatted_texts.append("")
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(formatted_texts))
    except IOError as e:
        logging.error(f"Error writing to output file: {e}")
        return
    
    logging.info(f"Formatted text has been written to {output_file_path}")
    
    print(f"Formatted text has been written to {output_file_path}")
