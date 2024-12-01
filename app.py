from flask import Flask, render_template, request, send_file, jsonify
import os
from datetime import datetime
import zipfile
from werkzeug.utils import secure_filename
import json
from main import get_template_placeholders, process_template
import csv
from models import Session, ZohoAccount
from email_sender import send_email, verify_email_credentials
from concurrent.futures import ThreadPoolExecutor
from functools import partial

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
    if not all(x in request.files for x in ['template', 'subject_template', 'csv']):
        return jsonify({'error': 'All files are required'}), 400
    
    template_file = request.files['template']
    subject_template_file = request.files['subject_template']
    csv_file = request.files['csv']
    
    if any(f.filename == '' for f in [template_file, subject_template_file, csv_file]):
        return jsonify({'error': 'No selected files'}), 400
    
    if not all(allowed_file(f.filename) for f in [template_file, subject_template_file, csv_file]):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save files
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                secure_filename(template_file.filename))
    subject_template_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                       secure_filename(subject_template_file.filename))
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                           secure_filename(csv_file.filename))
    
    template_file.save(template_path)
    subject_template_file.save(subject_template_path)
    csv_file.save(csv_path)
    
    # Get placeholders from both templates
    with open(template_path, 'r') as f:
        body_placeholders = get_template_placeholders(f.read())
    
    with open(subject_template_path, 'r') as f:
        subject_placeholders = get_template_placeholders(f.read())
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        csv_columns = reader.fieldnames
    
    return jsonify({
        'body_placeholders': list(body_placeholders),
        'subject_placeholders': list(subject_placeholders),
        'csv_columns': csv_columns,
        'template_path': template_path,
        'subject_template_path': subject_template_path,
        'csv_path': csv_path
    })

@app.route('/zoho-accounts', methods=['GET'])
def get_zoho_accounts():
    session = Session()
    accounts = session.query(ZohoAccount).all()
    return jsonify([{
        'id': acc.id,
        'email': acc.email,
        'is_active': acc.is_active,
        'sender_name': acc.sender_name,
    } for acc in accounts])

@app.route('/zoho-accounts', methods=['POST'])
def add_zoho_account():
    data = request.json
    session = Session()
    account = ZohoAccount(
        email=data['email'],
        app_password=data['app_password'],
        sender_name=data['sender_name']
    )
    session.add(account)
    try:
        session.commit()
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/zoho-accounts/<int:account_id>/toggle', methods=['POST'])
def toggle_account(account_id):
    session = Session()
    try:
        account = session.query(ZohoAccount).get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        account.is_active = not account.is_active
        session.commit()
        return jsonify({'success': True, 'is_active': account.is_active})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/process', methods=['POST'])
def process_files():
    data = request.json
    template_path = data['template_path']
    subject_template_path = data['subject_template_path']
    csv_path = data['csv_path']
    body_mapping = data['body_mapping']
    subject_mapping = data['subject_mapping']
    email_column = data['email_column']
    
    results = process_template(
        template_path,
        subject_template_path,
        csv_path,
        body_mapping,
        subject_mapping,
        email_column
    )
    
    session = Session()
    active_accounts = session.query(ZohoAccount).filter_by(is_active=1).all()
    
    if not active_accounts:
        return jsonify({'error': 'No active Zoho accounts found'}), 400

    # Send emails using rotating accounts
    current_account_index = 0
    success_count = 0
    failed_count = 0

    # First prepare all the account assignments
    email_tasks = []
    for i, result in enumerate(results):
        account = active_accounts[i % len(active_accounts)]
        email_tasks.append({
            'sender_email': account.email,
            'sender_password': account.app_password,
            'sender_name': account.sender_name,
            'recipient_email': result['recipient_email'],
            'subject': result['subject'],
            'body': result['body']
        })

    # Send emails in parallel using thread pool
    def send_email_task(task):
        try:
            send_email(**task)
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(send_email_task, email_tasks))
    
    success_count = sum(1 for r in results if r)
    failed_count = sum(1 for r in results if not r)

    return jsonify({
        'success_count': success_count,
        'failed_count': failed_count
    })

@app.route('/verify-accounts', methods=['POST'])
def verify_accounts():
    session = Session()
    try:
        accounts = session.query(ZohoAccount).all()
        results = {
            'verified': 0,
            'failed': 0,
            'total': len(accounts)
        }
        
        for account in accounts:
            is_valid = verify_email_credentials(account.email, account.app_password)
            if not is_valid and account.is_active:
                account.is_active = 0
                results['failed'] += 1
            elif is_valid:
                results['verified'] += 1
        
        session.commit()
        return jsonify(results)
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/zoho-accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    session = Session()
    try:
        account = session.query(ZohoAccount).get(id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
            
        session.delete(account)
        session.commit()
        return jsonify({'message': 'Account deleted successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True) 