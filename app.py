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
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def validate_excel_url(url):
    """Validate and potentially fix the Excel URL"""
    try:
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        
        # If no scheme is provided, add https://
        if not parsed.scheme:
            url = 'https://' + url
            
        # Try to make a HEAD request to check if the URL is accessible
        response = requests.head(url, allow_redirects=True, timeout=10)
        logger.info(f"URL validation response: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        return url, response.status_code == 200
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return url, False

def read_barcode(image):
    # Decode the barcode image
    decoded_objects = decode(image)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None

def read_excel_file(content):
    """Try different methods to read Excel file"""
    exceptions = []
    
    # Try openpyxl engine first (for .xlsx files)
    try:
        return pd.read_excel(BytesIO(content), engine='openpyxl')
    except Exception as e:
        exceptions.append(f"openpyxl error: {str(e)}")
    
    # Try xlrd engine (for older .xls files)
    try:
        return pd.read_excel(BytesIO(content), engine='xlrd')
    except Exception as e:
        exceptions.append(f"xlrd error: {str(e)}")
    
    # If both fail, raise the last exception with details
    raise Exception(f"Failed to read Excel file with all engines. Errors: {'; '.join(exceptions)}")

def check_serial_in_excel(serial_number, excel_url):
    try:
        logger.info(f"Checking serial number: {serial_number}")
        logger.info(f"Original Excel URL: {excel_url}")
        
        # Validate and potentially fix the URL
        excel_url, is_valid = validate_excel_url(excel_url)
        if not is_valid:
            logger.warning("URL validation failed")
            return False
            
        logger.info(f"Validated Excel URL: {excel_url}")
        
        # Configure requests session with appropriate headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Read Excel file from URL
        try:
            response = session.get(excel_url, timeout=30)
            logger.info(f"Excel response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Excel file. Status code: {response.status_code}")
                logger.warning(f"Response text: {response.text[:500]}...")
                return False
            
            # Try to read the Excel file using our helper function
            try:
                df = read_excel_file(response.content)
                logger.info(f"Successfully read Excel file")
                logger.info(f"Excel columns: {df.columns.tolist()}")
                logger.info(f"First few rows: {df.head().to_dict()}")
                
                # Clean up column names by removing whitespace and making them case-insensitive
                df.columns = [col.strip().lower() for col in df.columns]
                
                # Look for serial number column with various possible names
                serial_column = None
                possible_names = ['serialnumber', 'serial_number', 'serial', 'serial no', 'serial_no']
                
                for name in possible_names:
                    if name in df.columns:
                        serial_column = name
                        break
                
                if serial_column is None:
                    logger.warning("No serial number column found. Available columns: " + ", ".join(df.columns))
                    return False
                
                # Convert all values to string for comparison and clean them
                df[serial_column] = df[serial_column].astype(str).str.strip()
                serial_number = str(serial_number).strip()
                
                # Check if serial number exists in the Excel file
                result = serial_number in df[serial_column].values
                logger.info(f"Serial number found: {result}")
                
                # If not found, try case-insensitive search
                if not result:
                    logger.info(f"Sample values from serial column: {df[serial_column].head(10).tolist()}")
                    lower_serials = df[serial_column].str.lower()
                    if serial_number.lower() in lower_serials.values:
                        logger.info("Found with case-insensitive search!")
                        return True
                
                return result
                
            except Exception as e:
                logger.error(f"Error parsing Excel file: {str(e)}")
                traceback.print_exc(file=sys.stdout)
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("Request timed out while fetching Excel file")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking serial number: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok"}), 200

@app.route('/debug/excel')
def debug_excel():
    """Debug endpoint to inspect Excel file"""
    excel_url = os.getenv('EXCEL_URL')
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
        
    try:
        # Validate URL first
        excel_url, is_valid = validate_excel_url(excel_url)
        if not is_valid:
            return jsonify({
                'error': 'Invalid or inaccessible Excel URL',
                'url_tried': excel_url
            }), 400
            
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(excel_url, timeout=30)
        logger.info(f"Excel file request status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch Excel file. Status code: {response.status_code}',
                'response_text': response.text[:500],
                'headers': dict(response.headers),
                'url_tried': excel_url
            }), 400
            
        # Try to read the Excel file
        try:
            df = read_excel_file(response.content)
            
            # Clean up column names
            original_columns = df.columns.tolist()
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Get basic info about the Excel file
            info = {
                'status': 'success',
                'url': excel_url,
                'original_columns': original_columns,
                'cleaned_columns': df.columns.tolist(),
                'rows': len(df),
                'sample_data': df.head(5).to_dict(orient='records'),
                'response_headers': dict(response.headers),
                'content_type': response.headers.get('content-type', 'unknown')
            }
            
            # Look for serial number column
            possible_names = ['serialnumber', 'serial_number', 'serial', 'serial no', 'serial_no']
            found_column = None
            for name in possible_names:
                if name in df.columns:
                    found_column = name
                    break
            
            if found_column:
                info['serial_column_name'] = found_column
                info['serial_column_type'] = str(df[found_column].dtype)
                info['serial_sample'] = df[found_column].head(10).tolist()
            else:
                info['warning'] = f"No serial number column found. Available columns: {', '.join(df.columns)}"
                
            return jsonify(info)
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Failed to parse Excel file',
                'details': str(e),
                'url_tried': excel_url,
                'content_type': response.headers.get('content-type', 'unknown'),
                'content_preview': response.content[:100].hex()  # First 100 bytes in hex
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request timed out while fetching Excel file',
            'url_tried': excel_url
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'url_tried': excel_url
        }), 500

@app.route('/debug/check/<serial>')
def debug_check_serial(serial):
    """Debug endpoint to directly check a serial number"""
    excel_url = os.getenv('EXCEL_URL')
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
    
    try:
        is_valid = check_serial_in_excel(serial, excel_url)
        
        return jsonify({
            'status': 'success',
            'serial': serial,
            'valid': is_valid,
            'message': 'This product is from LG Syria' if is_valid else 'Product not found',
            'excel_url': excel_url
        })
    except Exception as e:
        logger.error(f"Error checking serial {serial}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Failed to check serial number: {str(e)}',
            'serial': serial,
            'excel_url': excel_url
        }), 500

@app.route('/check_serial', methods=['POST'])
def check_serial():
    serial_number = request.form.get('serial_number')
    excel_url = os.getenv('EXCEL_URL')  # Get Excel URL from environment variable
    
    if not excel_url:
        return jsonify({'error': 'Excel URL not configured'}), 400
    
    logger.info(f"Received request to check serial: {serial_number}")
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