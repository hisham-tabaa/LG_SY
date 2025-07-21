from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import pandas as pd
import requests
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Set secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

def read_barcode(image):
    # Decode the barcode image
    decoded_objects = decode(image)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None

def check_serial_in_excel(serial_number, excel_url):
    try:
        # Read Excel file from URL
        response = requests.get(excel_url)
        df = pd.read_excel(BytesIO(response.content))
        
        # Check if serial number exists in the Excel file
        # Assuming the column name is 'SerialNumber' - adjust as needed
        return serial_number in df['SerialNumber'].values
    except Exception as e:
        print(f"Error checking serial number: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok"}), 200

@app.route('/check_serial', methods=['POST'])
def check_serial():
    serial_number = request.form.get('serial_number')
    excel_url = os.getenv('EXCEL_URL')  # Get Excel URL from environment variable
    
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
    
    is_valid = check_serial_in_excel(serial_number, excel_url)
    
    return jsonify({
        'valid': is_valid,
        'message': 'This product is from LG Syria' if is_valid else 'Product not found'
    })

@app.route('/upload_barcode', methods=['POST'])
def upload_barcode():
    if 'barcode' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['barcode']
    excel_url = os.getenv('EXCEL_URL')
    
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
    
    # Read and process the image
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
    
    # Extract serial number from barcode
    serial_number = read_barcode(image)
    
    if not serial_number:
        return jsonify({'error': 'Could not read barcode'}), 400
    
    # Check serial number in Excel
    is_valid = check_serial_in_excel(serial_number, excel_url)
    
    return jsonify({
        'serial_number': serial_number,
        'valid': is_valid,
        'message': 'This product is from LG Syria' if is_valid else 'Product not found'
    })

if __name__ == '__main__':
    # Use environment variables for host and port if available
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug) 