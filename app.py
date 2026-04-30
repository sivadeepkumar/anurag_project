from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os
import json
import pandas as pd
import shutil
from werkzeug.utils import secure_filename
import json
import smtplib
from email.message import EmailMessage


# Get the absolute path to the template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['ATTACHMENTS_FOLDER'] = 'app/attachments'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
app.config['ALLOWED_ATTACHMENT_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'txt'}
app.config['FIXED_JSON_FILE'] = 'app/uploads/email_data.json'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['ATTACHMENTS_FOLDER']):
    os.makedirs(app.config['ATTACHMENTS_FOLDER'])

# Initialize the fixed JSON file if it doesn't exist
if not os.path.exists(app.config['FIXED_JSON_FILE']):
    with open(app.config['FIXED_JSON_FILE'], 'w') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_attachment(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_ATTACHMENT_EXTENSIONS']

@app.route('/')
def index():
    # Get list of all files in the uploads directory
    upload_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        upload_files = os.listdir(app.config['UPLOAD_FOLDER'])
    
    # Get list of all files in the attachments directory
    attachment_files = []
    if os.path.exists(app.config['ATTACHMENTS_FOLDER']):
        attachment_files = os.listdir(app.config['ATTACHMENTS_FOLDER'])
    
    # Check if email_data.json exists and load its data
    json_data = []
    if os.path.exists(app.config['FIXED_JSON_FILE']):
        try:
            with open(app.config['FIXED_JSON_FILE'], 'r') as f:
                json_data = json.load(f)
        except:
            pass
    
    return render_template('index.html', 
                          upload_files=upload_files, 
                          attachment_files=attachment_files, 
                          json_data=json_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file part'
        })
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No selected file'
        })
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Read Excel file
            excel_data = pd.read_excel(file_path)
            
            # Convert to JSON
            new_records = excel_data.to_dict(orient='records')
            
            # Add status field to each record
            for record in new_records:
                record['STATUS'] = 'READY'
                # Remove ATTACHMENT_STATUS field
                if 'ATTACHMENT_STATUS' in record:
                    del record['ATTACHMENT_STATUS']
                
                # If ATTACH_FILENAME doesn't exist, add a default empty value
                if 'ATTACH_FILENAME' not in record:
                    record['ATTACH_FILENAME'] = ''
            
            # Load existing data from the fixed JSON file
            json_data = []
            if os.path.exists(app.config['FIXED_JSON_FILE']):
                try:
                    with open(app.config['FIXED_JSON_FILE'], 'r') as f:
                        json_data = json.load(f)
                except:
                    json_data = []
            
            # Append new records to existing data
            json_data.extend(new_records)
            
            # Save to fixed JSON file
            with open(app.config['FIXED_JSON_FILE'], 'w') as f:
                json.dump(json_data, f, indent=4)
            
            return jsonify({
                'success': True,
                'data': json_data,
                'json_file': os.path.basename(app.config['FIXED_JSON_FILE']),
                'message': 'File successfully uploaded and converted to JSON'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': False,
            'error': 'File type not allowed'
        })

@app.route('/add_json_data', methods=['POST'])
def add_json_data():
    """Add JSON data directly to the fixed JSON file"""
    try:
        # Check if request contains JSON data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must contain JSON data'
            })
        
        # Get JSON data from request
        new_records = request.json
        
        # Convert to list if it's a single record
        if not isinstance(new_records, list):
            new_records = [new_records]
        
        # Add status field to each record if not already present
        for record in new_records:
            if 'STATUS' not in record:
                record['STATUS'] = 'READY'
            # Remove ATTACHMENT_STATUS field
            if 'ATTACHMENT_STATUS' in record:
                del record['ATTACHMENT_STATUS']
            if 'ATTACH_FILENAME' not in record:
                record['ATTACH_FILENAME'] = ''
        
        # Load existing data from the fixed JSON file
        json_data = []
        if os.path.exists(app.config['FIXED_JSON_FILE']):
            try:
                with open(app.config['FIXED_JSON_FILE'], 'r') as f:
                    json_data = json.load(f)
            except:
                json_data = []
        
        # Append new records to existing data
        json_data.extend(new_records)
        
        # Save to fixed JSON file
        with open(app.config['FIXED_JSON_FILE'], 'w') as f:
            json.dump(json_data, f, indent=4)
        
        return jsonify({
            'success': True,
            'data': json_data,
            'json_file': os.path.basename(app.config['FIXED_JSON_FILE']),
            'message': 'JSON data successfully added'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_json_data', methods=['GET'])
def get_json_data():
    """Get data from the fixed JSON file"""
    if os.path.exists(app.config['FIXED_JSON_FILE']):
        try:
            with open(app.config['FIXED_JSON_FILE'], 'r') as f:
                json_data = json.load(f)
            return jsonify({
                'success': True,
                'data': json_data,
                'json_file': os.path.basename(app.config['FIXED_JSON_FILE'])
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': False,
            'error': 'JSON file not found'
        })

@app.route('/upload_files', methods=['POST'])
def upload_files():
    uploaded_files = request.files.getlist('files[]')
    
    if not uploaded_files or len(uploaded_files) == 0 or uploaded_files[0].filename == '':
        return jsonify({
            'success': False,
            'error': 'No files uploaded'
        })
    
    saved_files = []
    error_files = []
    
    for file in uploaded_files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(file_path)
                saved_files.append(filename)
            except Exception as e:
                error_files.append({
                    'name': filename,
                    'error': str(e)
                })
    
    # Get updated list of all files in uploads directory
    all_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    
    return jsonify({
        'success': True,
        'saved_files': saved_files,
        'error_files': error_files,
        'all_files': all_files
    })

@app.route('/list_uploaded_files', methods=['GET'])
def list_uploaded_files():
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify({
            'success': True,
            'files': uploaded_files
        })
    return jsonify({
        'success': False,
        'files': []
    })

@app.route('/upload_attachments', methods=['POST'])
def upload_attachments():
    uploaded_files = request.files.getlist('attachments[]')
    
    if not uploaded_files or len(uploaded_files) == 0 or uploaded_files[0].filename == '':
        return jsonify({
            'success': False,
            'error': 'No files uploaded'
        })
    
    saved_files = []
    error_files = []
    
    for file in uploaded_files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['ATTACHMENTS_FOLDER'], filename)
            
            try:
                file.save(file_path)
                saved_files.append(filename)
            except Exception as e:
                error_files.append({
                    'name': filename,
                    'error': str(e)
                })
    
    # Get updated list of all files in attachments directory
    all_files = []
    if os.path.exists(app.config['ATTACHMENTS_FOLDER']):
        all_files = os.listdir(app.config['ATTACHMENTS_FOLDER'])
    
    return jsonify({
        'success': True,
        'saved_files': saved_files,
        'error_files': error_files,
        'all_files': all_files
    })

@app.route('/list_attachments', methods=['GET'])
def list_attachments():
    if os.path.exists(app.config['ATTACHMENTS_FOLDER']):
        attachment_files = os.listdir(app.config['ATTACHMENTS_FOLDER'])
        return jsonify({
            'success': True,
            'files': attachment_files
        })
    return jsonify({
        'success': False,
        'files': []
    })

@app.route('/verify_attachment', methods=['POST'])
def verify_attachment():
    """Check if a file exists in the attachments folder"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing filename in request body'
            })
        
        filename = data['filename']
        file_path = os.path.join(app.config['ATTACHMENTS_FOLDER'], filename)
        
        file_exists = os.path.exists(file_path)
        
        return jsonify({
            'success': True,
            'exists': file_exists
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/update_attachment_status', methods=['POST'])
def update_attachment_status():
    # This endpoint is no longer needed since we're removing ATTACHMENT_STATUS
    return jsonify({
        'success': False,
        'error': 'This endpoint is deprecated'
    })

@app.route('/delete_file', methods=['DELETE'])
def delete_file():
    filename = request.args.get('filename')
    file_type = request.args.get('type')
    
    if not filename:
        return jsonify({
            'success': False,
            'error': 'Filename is required'
        })
    
    if file_type == 'upload':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    elif file_type == 'attachment':
        file_path = os.path.join(app.config['ATTACHMENTS_FOLDER'], filename)
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid file type'
        })
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': f'File {filename} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/update_json_data', methods=['POST'])
def update_json_data():
    data = request.json
    if not data or 'data' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        })
    
    updated_data = data['data']
    
    # Check if the file exists
    json_path = app.config['FIXED_JSON_FILE']
    if not os.path.exists(json_path):
        return jsonify({
            'success': False,
            'error': 'JSON file not found'
        })
    
    try:
        # Save the updated JSON file
        with open(json_path, 'w') as json_file:
            json_file.write(json.dumps(updated_data, indent=4))
        
        return jsonify({
            'success': True,
            'message': 'JSON data updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })



@app.route('/update_record', methods=['POST'])
def update_record():
    """Update a single record in the JSON data"""
    try:
        data = request.json
        if not data or 'record_id' not in data or 'record_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            })
        
        record_id = int(data['record_id'])
        record_data = data['record_data']
        
        # Load existing data
        with open(app.config['FIXED_JSON_FILE'], 'r') as f:
            json_data = json.load(f)
        
        # Validate record_id
        if record_id < 0 or record_id >= len(json_data):
            return jsonify({
                'success': False,
                'error': 'Invalid record ID'
            })
        
        # Update the record
        json_data[record_id] = record_data
        
        # Save updated data
        with open(app.config['FIXED_JSON_FILE'], 'w') as f:
            json.dump(json_data, f, indent=4)
        
        return jsonify({
            'success': True,
            'data': json_data,
            'message': 'Record updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    print("📥 Received data:", data)

    try:
        # Extract sender details
        sender_email = data['sender_email']
        app_password = data['app_password']


        print("✅ Sender Email:", sender_email)


        # Load recipients from file
        with open('app/uploads/email_data.json', 'r') as file:
            recipients = json.load(file)

        print(f"📄 Loaded {len(recipients)} recipients from JSON")

        for recipient in recipients:
            print(recipient)
            try:
                name = recipient.get('NAME', 'Recipient')
                to_email = recipient['SENDER_EMAIL']
                filename = recipient['ATTACH_FILENAME']
                subject = recipient['SUBJECT']
                context = recipient['CONTEXT']
                # status = recipient.get('STATUS', 'READY')

                print(f"📨 Sending to: {to_email} ({name})")

                # Compose email
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = to_email
                msg.set_content(
                    f"Dear {name},\n\n"
                    "Thank you for attending the Micromedex Training Program held on March 25, 2026. "
                    "We hope you found the session informative and valuable in enhancing your understanding of "
                    "Micromedex and its applications in clinical decision-making and research.\n\n"
                    "Please find attached your Certificate of Participation, presented as a token of appreciation "
                    "for your valuable participation.\n\n"
                    "Wishing you continued success in your academic and professional journey!\n\n"
                    "Thanks & Regards\n"
                    "www.daiknow.com"
                )
                msg.add_alternative(
                    f"""\
<html>
  <body style="font-family: Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #111111;">
    <p style="margin: 0 0 12px 0;">Dear {name},</p>
    <p style="margin: 0 0 12px 0;">
      Thank you for attending the <strong>Micromedex Training Program</strong> held on
      <strong>March 25, 2026</strong>. We hope you found the session informative and valuable in
      enhancing your understanding of Micromedex and its applications in clinical decision-making
      and research.
    </p>
    <p style="margin: 0 0 12px 0;">
      Please find attached your <strong>Certificate of Participation</strong>, presented as a token
      of appreciation for your valuable participation.
    </p>
    <p style="margin: 0 0 12px 0;">Wishing you continued success in your academic and professional journey!</p>
    <p style="margin: 0 0 8px 0;">Thanks &amp; Regards</p>
    <p style="margin: 0 0 8px 0;">
      <img width="96" height="81" src="https://ci3.googleusercontent.com/mail-sig/AIorK4yK_lh6u1pZs7ZpBhqlf7MKfgdftJkvWpA-etPsSpwNAEs919bLj0_fC9qVSdVJCVnr5kZLl9aktuYI" alt="Signature image">
    </p>
    <p style="margin: 0;"><a href="https://www.daiknow.com/" style="color: #1a73e8;">www.daiknow.com</a></p>
  </body>
</html>
""",
                    subtype='html'
                )

                # Attach file
                attachment_path = os.path.join('app', 'attachments', filename)
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment_path)
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                    print(f"📎 Attached: {file_name}")
                else:
                    print(f"⚠️ File not found: {attachment_path}")
                    continue  # Skip this recipient

                # Send email using Gmail SMTP
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(sender_email, app_password)
                    smtp.send_message(msg)
                    print(f"✅ Email sent to: {to_email}")

            except Exception as e:
                print(f"❌ Failed to send to {recipient.get('SENDER_EMAIL')}: {str(e)}")
                continue

        return jsonify({'success': True, 'message': 'Emails sent successfully'}), 200

    except KeyError as e:
        return jsonify({'success': False, 'error': f'Missing key: {e}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5175, debug=True)
