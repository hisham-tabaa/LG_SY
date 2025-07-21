from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import pandas as pd
import requests
from io import BytesIO
import os
import sys
import traceback
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
        print(f"Checking serial number: {serial_number}")
        print(f"Excel URL: {excel_url}")
        
        # Read Excel file from URL
        response = requests.get(excel_url)
        print(f"Excel response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch Excel file. Status code: {response.status_code}")
            return False
        
        # Try to read the Excel file
        try:
            df = pd.read_excel(BytesIO(response.content))
            print(f"Excel columns: {df.columns.tolist()}")
            print(f"First few rows: {df.head().to_dict()}")
            
            # Check if SerialNumber column exists
            if 'SerialNumber' not in df.columns:
                print("Warning: 'SerialNumber' column not found in Excel file.")
                # Try to find a column that might contain serial numbers
                possible_columns = [col for col in df.columns if 'serial' in col.lower()]
                if possible_columns:
                    print(f"Using column {possible_columns[0]} instead")
                    return serial_number in df[possible_columns[0]].astype(str).values
                else:
                    print("No suitable column found for serial numbers")
                    return False
            
            # Convert all values to string for comparison
            df['SerialNumber'] = df['SerialNumber'].astype(str)
            
            # Check if serial number exists in the Excel file
            result = serial_number in df['SerialNumber'].values
            print(f"Serial number found: {result}")
            
            # If not found, print some nearby values for debugging
            if not result:
                print(f"Sample values from SerialNumber column: {df['SerialNumber'].head(10).tolist()}")
                # Try case-insensitive search
                lower_serials = df['SerialNumber'].str.lower()
                if serial_number.lower() in lower_serials.values:
                    print("Found with case-insensitive search!")
                    return True
            
            return result
            
        except Exception as e:
            print(f"Error parsing Excel file: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return False
            
    except Exception as e:
        print(f"Error checking serial number: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok"}), 200

@app.route('/debug/excel', methods=['GET'])
def debug_excel():
    """Debug endpoint to inspect Excel file"""
    if not os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
        return jsonify({"error": "Debug mode not enabled"}), 403
        
    excel_url = os.getenv('EXCEL_URL')
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
        
    try:
        response = requests.get(excel_url)
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch Excel file. Status code: {response.status_code}'
            }), 400
            
        df = pd.read_excel(BytesIO(response.content))
        
        # Get basic info about the Excel file
        info = {
            'columns': df.columns.tolist(),
            'rows': len(df),
            'sample_data': df.head(5).to_dict(orient='records'),
        }
        
        # If SerialNumber column exists, provide some stats
        if 'SerialNumber' in df.columns:
            info['serial_column_type'] = str(df['SerialNumber'].dtype)
            info['serial_sample'] = df['SerialNumber'].head(10).tolist()
            
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/check/<serial>', methods=['GET'])
def debug_check_serial(serial):
    """Debug endpoint to directly check a serial number"""
    if not os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
        return jsonify({"error": "Debug mode not enabled"}), 403
        
    excel_url = os.getenv('EXCEL_URL')
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
        
    is_valid = check_serial_in_excel(serial, excel_url)
    
    return jsonify({
        'serial': serial,
        'valid': is_valid,
        'message': 'This product is from LG Syria' if is_valid else 'Product not found'
    })

@app.route('/check_serial', methods=['POST'])
def check_serial():
    serial_number = request.form.get('serial_number')
    excel_url = os.getenv('EXCEL_URL')  # Get Excel URL from environment variable
    
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
    
    print(f"Received request to check serial: {serial_number}")
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