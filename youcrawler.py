from flask import Flask, render_template, request, redirect, url_for, send_from_directory , jsonify
import scrapetube
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NotTranslatable, TranscriptsDisabled, VideoUnavailable, CouldNotRetrieveTranscript, NoTranscriptAvailable
from youtube_transcript_api._errors import CookiePathInvalid, CookiesInvalid, CouldNotRetrieveTranscript, FailedToCreateConsentCookie, InvalidVideoId, NoTranscriptAvailable, NoTranscriptFound, NotTranslatable, TooManyRequests, TranscriptsDisabled, VideoUnavailable, YouTubeRequestFailed
import logging
import os
import utils

app = Flask(__name__)

# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'raw_data')

def extract_title(video_info):
    """Extracts the title from the nested video info dictionary."""
    try:
        title_parts = video_info.get('title', {}).get('runs', [{}])
        title = title_parts[0].get('text', 'No title available')
        return title
    except (AttributeError, IndexError, KeyError):
        return 'No title available'

def get_transcripts(video_ids):
    transcripts = {}
    for video_id in video_ids:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcripts[video_id] = transcript
        except VideoUnavailable:
            transcripts[video_id] = "Transcript not available"
        except TranscriptsDisabled:
            transcripts[video_id] = "Transcripts disabled"
        except NotTranslatable:
            transcripts[video_id] = "Not Translatable"
        # except CouldNotRetrieveTranscript:
        #     transcripts[video_id] = "Could Not Retrieve Transcript"
        except InvalidVideoId:
            transcripts[video_id] = "invalid video ID"
        except NoTranscriptAvailable:
            transcripts[video_id] = "No Transcript Available"
        except NoTranscriptFound:
            transcripts[video_id] = "No Transcript Found"
        except TooManyRequests:
            transcripts[video_id] = "Too Many Requests"     
        except Exception as e:
            transcripts[video_id] = f"Error: {e}"

    return transcripts

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        content_type = request.form['content_type']
        
        # Ensure the 'raw_data' directory exists
        if not os.path.exists(RAW_DATA_DIR):
            os.makedirs(RAW_DATA_DIR)

        videos = scrapetube.get_channel(channel_username=username, content_type=content_type)

        video_links = {}
        video_ids = []

        for video in videos:
            video_id = video.get('videoId')
            video_title = extract_title(video)

            if not isinstance(video_title, str):
                video_title = 'No title available'
            
            video_link = f"https://www.youtube.com/watch?v={video_id}"
            
            video_links[video_title] = {
                "link": video_link,
                "videoId": video_id,
                "transcript": None
            }
            video_ids.append(video_id)

        transcripts = get_transcripts(video_ids)

        for video_title, video_info in video_links.items():
            video_id = video_info.get('videoId')
            if video_id:
                transcript = transcripts.get(video_id)
                video_links[video_title]["transcript"] = transcript

        json_file_path = os.path.join(RAW_DATA_DIR, 'video_links_with_transcripts.json')
        try:
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(video_links, json_file, indent=4, ensure_ascii=False)
        except IOError as e:
            app.logger.error(f"Error writing JSON file: {e}")
            return "Error writing JSON file", 500

        return redirect(url_for('process_page'))

    return render_template('index.html')

@app.route('/process')
def process_page():
    return render_template('process.html')

@app.route('/process_data', methods=['POST'])
def process_data():
    json_file_path = os.path.join(RAW_DATA_DIR, 'video_links_with_transcripts.json')
    
    if not os.path.exists(json_file_path):
        return "JSON file not found", 404

    # Load the JSON data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        return f"Error loading JSON file: {e}", 500

    # Return the JSON data and a flag indicating that processing is not started yet
    return jsonify({
        'data': data,
        'status': 'ready'  # Status to indicate the data is ready to be processed
    })
@app.route('/start_processing', methods=['POST'])
def start_processing():
    json_file_path = os.path.join(RAW_DATA_DIR, 'video_links_with_transcripts.json')
    output_text_file = os.path.join(RAW_DATA_DIR, 'output_transcripts.txt')

    logging.info(f"Processing data from {json_file_path} to {output_text_file}")

    # Process the file
    try:
        utils.process_transcripts(json_file_path, output_text_file)
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        return "Processing error", 500

    if not os.path.exists(output_text_file) or os.stat(output_text_file).st_size == 0:
        logging.error(f"Output file not generated or is empty: {output_text_file}")
        return "Output file not generated", 500

    logging.info("Processing complete. Redirecting to results.")
    return jsonify({
        'status': 'processed',
        'file_url': url_for('download_file', filename='output_transcripts.txt')
    })

@app.route('/fetch_output')
def fetch_output():
    # Path to the log file or real-time output file
    log_file_path = os.path.join(RAW_DATA_DIR, 'process_log.txt')

    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as file:
            return file.read()
    return "No output yet."

@app.route('/result')
def result():
    return render_template('result.html', file_url=url_for('download_file', filename='output_transcripts.txt'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(RAW_DATA_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
