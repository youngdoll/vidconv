from flask import Flask, request, render_template, send_file, jsonify
import os
import yt_dlp
import subprocess

app = Flask(__name__)

# Создаем папку для временных файлов
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")

# Функция загрузки видео с YouTube
def download_video(url, format):
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best" if format == "mp4" else "bestaudio",
        "merge_output_format": "mp4" if format == "mp4" else "mp3",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_name = ydl.prepare_filename(info)
        return file_name.replace(".webm", ".mp4") if format == "mp4" else file_name.replace(".webm", ".mp3")

@app.route("/convert", methods=["POST"])
def convert():
    url = request.form.get("url")
    format = request.form.get("format")

    if format not in ["mp4", "mp3"]:
        return jsonify({"error": "Неподдерживаемый формат"}), 400

    try:
        file_path = download_video(url, format)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
