from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import subprocess

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_video_info(url):
    """Получаем информацию о видео"""
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/bestvideo',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        'title': info.get('title', 'Без названия'),
        'duration': info.get('duration', 0),
        'formats': [{'format_id': f['format_id'], 'ext': f['ext']} for f in info['formats']]
    }

def download_video(url, format_id):
    """Скачивание видео"""
    output_file = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
    ydl_opts = {
        'quiet': True,
        'format': format_id,
        'outtmpl': output_file,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return os.path.join(DOWNLOAD_FOLDER, f"{info['title']}.{info['ext']}")

def convert_to_mp3(input_file):
    """Конвертация в MP3"""
    output_file = input_file.rsplit('.', 1)[0] + ".mp3"
    cmd = ["ffmpeg", "-i", input_file, "-vn", "-ab", "192k", "-y", output_file]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL не указан'}), 400
    try:
        info = get_video_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get("url")
    format_id = data.get("format")

    if not url or not format_id:
        return jsonify({'error': 'URL или формат не указан'}), 400

    try:
        file_path = download_video(url, format_id)
        if data.get("convert_to_mp3"):
            file_path = convert_to_mp3(file_path)
        return jsonify({'file': file_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_file')
def download_file():
    file_path = request.args.get("file")
    if not file_path or not os.path.exists(file_path):
        return "Файл не найден", 404
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)