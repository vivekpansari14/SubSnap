from flask import Flask, render_template, request, send_from_directory
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
SUBTITLE_FOLDER = 'static/subtitles'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUBTITLE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_subtitle', methods=['POST'])
def generate_subtitle():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = str(uuid.uuid4()) + file_ext
    uploaded_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(uploaded_path)

    output_srt_path = os.path.splitext(uploaded_path)[0]
    final_srt_filename = os.path.splitext(unique_filename)[0] + ".srt"
    final_srt_path = os.path.join(SUBTITLE_FOLDER, final_srt_filename)

    # Example settings for delay, max_words, etc. — customize if needed
    os.system(f"python3 newmain.py '{uploaded_path}' 0.3 10 2 yellow 20")

    if not os.path.exists(output_srt_path + ".srt"):
        return "Subtitle generation failed", 500

    os.rename(output_srt_path + '.srt', final_srt_path)

    return {"subtitle_url": f"/static/subtitles/{final_srt_filename}"}

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
