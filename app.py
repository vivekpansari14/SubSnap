from flask import Flask, render_template, request, jsonify
import os
import subprocess
import uuid
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
SUBTITLE_FOLDER = os.path.join('static', 'subtitles')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUBTITLE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_subtitle', methods=['POST'])
def generate_subtitle():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = str(uuid.uuid4()) + file_ext
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    output_name = str(uuid.uuid4())
    output_srt_path = os.path.join(UPLOAD_FOLDER, output_name)

    # Call your existing subtitle generation script
    subprocess.run(['python3', 'newmain.py', '--input', file_path, '--output', output_srt_path])

    # Rename and move the generated file to static/subtitles
    final_srt_name = output_name + '.srt'
    final_srt_path = os.path.join(SUBTITLE_FOLDER, final_srt_name)
    os.rename(output_srt_path + '.srt', final_srt_path)

    # Create the download URL
    download_url = f"/{final_srt_path.replace(os.sep, '/')}"

    return jsonify({'download_url': download_url})

if __name__ == '__main__':
    app.run(debug=True)
