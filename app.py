from flask import Flask, request, render_template, send_file, jsonify
import os
import yt_dlp
import threading

app = Flask(__name__)

# Папка для временных файлов
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Функция загрузки видео
def download_video(url, format, callback):
    try:
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "bestvideo+bestaudio/best" if format == "mp4" else "bestaudio",
            "merge_output_format": format,
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}] if format == "mp4" else [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format == "mp4":
                file_path = file_path.rsplit(".", 1)[0] + ".mp4"
            elif format == "mp3":
                file_path = file_path.rsplit(".", 1)[0] + ".mp3"
            
            callback(file_path)
    except Exception as e:
        callback(None, str(e))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    url = request.form.get("url")
    format = request.form.get("format")

    if format not in ["mp4", "mp3"]:
        return jsonify({"error": "Неподдерживаемый формат"}), 400

    result = {"file_path": None, "error": None}

    def callback(path, error=None):
        result["file_path"] = path
        result["error"] = error

    thread = threading.Thread(target=download_video, args=(url, format, callback))
    thread.start()
    thread.join()  # Ждём завершения загрузки

    if result["error"]:
        return jsonify({"error": result["error"]}), 500
    if not result["file_path"]:
        return jsonify({"error": "Ошибка загрузки"}), 500

    return send_file(result["file_path"], as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
