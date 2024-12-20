from flask import Flask, request, send_file, jsonify
import yt_dlp as ytdlp
import os
from flask_cors import CORS
import re

# Define the Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@app.route('/download', methods=['POST'])
def download_video():
    try:
        # Get the video URL from the request body
        data = request.get_json()
        video_url = data.get('url')

        # Check if the URL is provided
        if not video_url:
            return jsonify({"success": False, "error": "Missing URL"}), 400

        # Set options for yt-dlp
        download_path = "downloads"
        os.makedirs(download_path, exist_ok=True)

        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),  # Save video in 'downloads' folder
            'noplaylist': True,  # Don't download playlists, just the video
            'quiet': False,  # Show progress and debug information
        }

        # Hook to get the filename after downloading
        def post_process(info):
            filename = os.path.join(download_path, f"{sanitize_filename(info['title'])}.mp4")
            return filename

        # Create a YouTube downloader object
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = post_process(info)

        # Verify the file size
        if os.path.getsize(downloaded_file) < 1024:  # Less than 1KB
            raise Exception("Downloaded file size is too small, indicating an issue with the download.")

        # Send the video file as a response
        return send_file(downloaded_file, as_attachment=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
