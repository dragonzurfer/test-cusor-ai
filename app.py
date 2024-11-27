from flask import Flask, render_template, request, send_file, jsonify
import os
from datetime import datetime
import zipfile
from werkzeug.utils import secure_filename
import json
from main import get_template_placeholders, process_template
import csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'csv'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'template' not in request.files or 'csv' not in request.files:
        return jsonify({'error': 'Both files are required'}), 400
    
    template_file = request.files['template']
    csv_file = request.files['csv']
    
    if template_file.filename == '' or csv_file.filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    if not (allowed_file(template_file.filename) and allowed_file(csv_file.filename)):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save files with secure filenames
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                secure_filename(template_file.filename))
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                           secure_filename(csv_file.filename))
    
    template_file.save(template_path)
    csv_file.save(csv_path)
    
    # Get placeholders and CSV columns
    with open(template_path, 'r') as f:
        template_content = f.read()
    placeholders = get_template_placeholders(template_content)
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        csv_columns = reader.fieldnames
    
    return jsonify({
        'placeholders': list(placeholders),
        'csv_columns': csv_columns,
        'template_path': template_path,
        'csv_path': csv_path
    })

@app.route('/process', methods=['POST'])
def process_files():
    data = request.json
    template_path = data['template_path']
    csv_path = data['csv_path']
    mapping = data['mapping']
    
    results = process_template(template_path, csv_path, mapping)
    
    # Create ZIP file
    timestamp = datetime.now().strftime('%Y%m%d')
    zip_filename = f'download_template_{timestamp}.zip'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i, result in enumerate(results, 1):
            zipf.writestr(f'output_{i}.txt', result)
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 