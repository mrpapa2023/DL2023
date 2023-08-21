from flask import Flask, render_template, request, jsonify
import os
import subprocess
import threading
import time
import zipfile
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.static_folder = 'static'

token_available = False
execution_1_completed = False
execution_2_completed = False

app.debug = True
UPLOAD_FOLDER = './'
ALLOWED_EXTENSIONS = {'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_credentials', methods=['POST'])
def upload_credentials():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part"})

    file = request.files['file']

    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})

    if file and allowed_file(file.filename):
        filename = 'credentials.json'  # Save as credentials.json
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"success": True, "message": "File uploaded successfully"})
    else:
        return jsonify({"success": False, "message": "Invalid file format"})
    
def check_token():
    global token_available, execution_2_completed
    while True:
        if os.path.exists('token.json'):
            token_available = True
            subprocess.run(['python', '2.py'])
            execution_2_completed = True
            break
        time.sleep(1)

def run_1_script():
    global execution_1_completed
    # Run 1.py
    subprocess.run(['python', '1.py'])
    execution_1_completed = True

def get_directory_contents(excluded_folders=["static", "templates","__pycache__"]):
    data = []
    for root, dirs, files in os.walk("."):
        # Exclude specified folders
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        
        if root != ".":
            directory = os.path.basename(root)
            file_names = [f for f in files if os.path.basename(root) not in excluded_folders]
            data.append({"directory": directory, "files": file_names})
    return data



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    global token_available, execution_1_completed, execution_2_completed

    # Delete token.json
    if os.path.exists('token.json'):
        os.remove('token.json')

    # Reset flags
    token_available = False
    execution_1_completed = False
    execution_2_completed = False

    # Start token availability check
    token_thread = threading.Thread(target=check_token)
    token_thread.start()

    # Start 1.py execution
    script_thread = threading.Thread(target=run_1_script)
    script_thread.start()

    return "Download started"

@app.route('/get_directory_contents')
def get_directory_contents_route():
    data = get_directory_contents()
    return jsonify(data)

@app.route('/check_end')
def check_end():
    if execution_1_completed and execution_2_completed:
        return jsonify(True)
    return jsonify(False)

def add_folder_to_zip(zipf, folder_path, folder_name):
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.join(folder_name, os.path.relpath(file_path, folder_path))
            zipf.write(file_path, arcname=arcname)

@app.route('/create_zip', methods=['POST'])
def create_zip():
    data = request.json
    file_name = data.get('fileName')

    if not file_name:
        return jsonify({"success": False, "message": "Invalid file name."})

    try:
        with zipfile.ZipFile(f'{file_name}.zip', 'w') as zipf:
            # Add contents of Gmail and GDrive folders to the zip file
            add_folder_to_zip(zipf, 'Gmail', 'Gmail')
            add_folder_to_zip(zipf, 'GDrive', 'GDrive')
            
        return jsonify({"success": True, "message": "Zip file created successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run()
