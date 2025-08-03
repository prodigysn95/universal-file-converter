from flask import Flask, render_template, request, send_file, jsonify
import os
import zipfile
from datetime import datetime
from threading import Thread
import subprocess
import re
from converter_lite import convert_image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress_data = {
    "status": "",
    "progress": 0,
    "batch_id": None,
    "files": []
}

def get_media_duration(file_path):
    """Dapatkan durasi file (detik) pakai ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return None

def convert_video_with_progress(input_file, output_file):
    total_duration = get_media_duration(input_file)
    cmd = [
        "ffmpeg", "-i", input_file, output_file,
        "-y", "-progress", "pipe:1", "-nostats"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        if "out_time_ms" in line and total_duration:
            value = line.strip().split("=")[1]
            if value.isdigit():
                ms = int(value)
                seconds = ms / 1_000_000
                percent = int((seconds / total_duration) * 100)
                progress_data["progress"] = min(percent, 99)
    process.wait()
    progress_data["progress"] = 100

def run_conversion(batch_id, files, mode, format_out):
    progress_data["status"] = "converting"
    progress_data["progress"] = 0
    total_files = len(files)
    output_files = []

    batch_folder = os.path.join(OUTPUT_FOLDER, batch_id)
    os.makedirs(batch_folder, exist_ok=True)

    for idx, file_info in enumerate(files):
        filename = file_info["filename"]
        filepath = file_info["path"]
        output_filename = f"{os.path.splitext(filename)[0]}.{format_out}"
        output_path = os.path.join(batch_folder, output_filename)

        if mode == "image":
            convert_image(filepath, format_out, output_path)
            progress_data["progress"] = int(((idx + 1) / total_files) * 100)
        elif mode in ["video", "audio"]:
            convert_video_with_progress(filepath, output_path)

        output_files.append(output_filename)

    progress_data["files"] = output_files
    progress_data["status"] = "done"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    mode = request.form["mode"]
    format_out = request.form["format"]

    batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
    uploaded_files = []

    progress_data["status"] = "uploading"
    progress_data["progress"] = 0
    progress_data["batch_id"] = batch_id
    progress_data["files"] = []

    files = request.files.getlist("files")
    total = len(files)

    for idx, file in enumerate(files):
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)
        uploaded_files.append({"filename": file.filename, "path": input_path})
        progress_data["progress"] = int(((idx + 1) / total) * 100)

    thread = Thread(target=run_conversion, args=(batch_id, uploaded_files, mode, format_out))
    thread.start()

    return jsonify({"batch_id": batch_id})

@app.route("/progress")
def progress():
    return jsonify(progress_data)

@app.route("/download/<batch_id>/<filename>")
def download_file(batch_id, filename):
    return send_file(os.path.join(OUTPUT_FOLDER, batch_id, filename), as_attachment=True)

@app.route("/download_zip/<batch_id>")
def download_zip(batch_id):
    batch_folder = os.path.join(OUTPUT_FOLDER, batch_id)
    zip_path = os.path.join(OUTPUT_FOLDER, f"{batch_id}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(batch_folder):
            zipf.write(os.path.join(batch_folder, file), file)
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
