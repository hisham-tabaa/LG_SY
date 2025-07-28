from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from io import BytesIO
import os
import logging
import re
import traceback
from dotenv import load_dotenv
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Translations for responses
translations = {
    'en': {
        'success': 'This product is from LG Syria',
        'not_found': 'Product not found',
        'error_excel': 'Excel URL not configured',
        'error_ocr': 'Image processing is currently unavailable. Please enter the serial number manually.',
        'error_file': 'No file uploaded',
        'product_details': 'Product Details',
        'serial_number': 'Serial Number',
        'product_name': 'Product Name',
        'product_description': 'Product Description'
    },
    'ar': {
        'success': 'هذا المنتج من إل جي سوريا',
        'not_found': 'المنتج غير موجود',
        'error_excel': 'لم يتم تكوين عنوان URL لملف Excel',
        'error_ocr': 'معالجة الصور غير متاحة حاليًا. يرجى إدخال الرقم التسلسلي يدويًا.',
        'error_file': 'لم يتم تحميل أي ملف',
        'product_details': 'تفاصيل المنتج',
        'serial_number': 'الرقم التسلسلي',
        'product_name': 'اسم المنتج',
        'product_description': 'وصف المنتج'
    }
}

# Simple OCR availability check (simplified)
try:
    import pytesseract
    import subprocess
    # Quick check if tesseract is available
    result = subprocess.run(['tesseract', '--version'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                           check=False, timeout=5)
    OCR_AVAILABLE = result.returncode == 0
    if OCR_AVAILABLE:
        logger.info("OCR functionality is available")
    else:
        logger.info("Tesseract not found - OCR functionality disabled")
except Exception as e:
    OCR_AVAILABLE = False
    logger.info(f"OCR functionality disabled: {str(e)}")

# Load environment variables
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

def get_message(key, lang='en'):
    """Get translated message"""
    if lang not in translations:
        lang = 'en'
    return translations[lang].get(key, translations['en'].get(key, ''))

def validate_excel_url(url):
    """Validate and potentially fix the Excel URL"""
    try:
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        
        # Handle Google Sheets URLs
        if 'docs.google.com' in parsed.netloc and '/spreadsheets/d/' in parsed.path:
            # Extract the document ID
            parts = parsed.path.split('/')
            for i, part in enumerate(parts):
                if part == 'd' and i+1 < len(parts):
                    doc_id = parts[i+1]
                    # Create a direct export URL
                    export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                    logger.info(f"Converted Google Sheets URL to export URL: {export_url}")
                    url = export_url
                    break
        
        # If no scheme is provided, add https://
        if not parsed.scheme:
            url = 'https://' + url
            
        # Try to make a HEAD request to check if the URL is accessible
        response = requests.head(url, allow_redirects=True, timeout=10)
        logger.info(f"URL validation response: {response.status_code}")
        
        return url, response.status_code == 200
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return url, False

def normalize_serial(s):
    """Normalize serial number for comparison"""
    if not isinstance(s, str):
        s = str(s)
    return ''.join(s.split()).upper()

def read_excel_file(content):
    """Try different methods to read Excel file with proper encoding"""
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
    raise Exception(f"Failed to read Excel file. Errors: {'; '.join(exceptions)}")

def check_serial_in_excel(serial_number, excel_url):
    """Check if serial number exists in Excel file"""
    try:
        logger.info(f"Checking serial number: {serial_number}")
        
        # Validate and potentially fix the URL
        excel_url, is_valid = validate_excel_url(excel_url)
        if not is_valid:
            logger.warning("URL validation failed")
            return False, None, None
            
        logger.info(f"Validated Excel URL: {excel_url}")
        
        # Configure requests session with appropriate headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Read Excel file from URL
        response = session.get(excel_url, timeout=30)
        logger.info(f"Excel response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch Excel file. Status code: {response.status_code}")
            return False, None, None
        
        # Try to read the Excel file
        df = read_excel_file(response.content)
        logger.info(f"Successfully read Excel file with {len(df)} rows")
        logger.info(f"Excel columns: {df.columns.tolist()}")
        
        # Clean up column names by removing whitespace
        df.columns = [col.strip() for col in df.columns]
        logger.info(f"Cleaned Excel columns: {df.columns.tolist()}")
        
        # Create a case-insensitive mapping for column names
        column_map = {col.lower(): col for col in df.columns}
        
        # Look for serial number column with various possible names
        serial_column = None
        possible_serial_names = ['serialnumber', 'serial_number', 'serial', 'serial no', 'serial_no', 
                               'الرقم التسلسلي', 'رقم تسلسلي', 'الرقم_التسلسلي']
        
        for name in possible_serial_names:
            # Try exact match first
            if name in df.columns:
                serial_column = name
                break
            # Try case-insensitive match
            elif name.lower() in column_map:
                serial_column = column_map[name.lower()]
                break
        
        if serial_column is None:
            # Last resort: try to find any column that contains "serial" or "رقم"
            for col in df.columns:
                if "serial" in col.lower() or "رقم" in col:
                    serial_column = col
                    break
        
        if serial_column is None:
            logger.warning("No serial number column found. Available columns: " + ", ".join(df.columns))
            return False, None, None
        
        # Look for product name column (اسم المادة)
        product_name_column = None
        possible_name_columns = ['اسم المادة', 'اسم_المادة', 'product_name', 'name', 'productname', 'product']
        
        for name in possible_name_columns:
            if name in df.columns:
                product_name_column = name
                logger.info(f"Found product name column: {product_name_column}")
                break
            elif name.lower() in column_map:
                product_name_column = column_map[name.lower()]
                logger.info(f"Found product name column (case-insensitive): {product_name_column}")
                break
        
        # Look for product code/description column (رمز المادة)
        product_desc_column = None
        possible_desc_columns = ['رمز المادة', 'رمز_المادة', 'product_code', 'material_code', 'code', 
                               'description', 'product_description', 'desc']
        
        for name in possible_desc_columns:
            if name in df.columns:
                product_desc_column = name
                logger.info(f"Found product description/code column: {product_desc_column}")
                break
            elif name.lower() in column_map:
                product_desc_column = column_map[name.lower()]
                logger.info(f"Found product description/code column (case-insensitive): {product_desc_column}")
                break
        
        # Log final column assignments
        logger.info(f"Column assignments - Serial: {serial_column}, Name: {product_name_column}, Description/Code: {product_desc_column}")
        
        # Convert serial numbers to string for comparison and clean them
        df[serial_column] = df[serial_column].astype(str).str.strip()
        serial_number = str(serial_number).strip()
        
        # Normalize for robust matching
        df['serial_normalized'] = df[serial_column].apply(normalize_serial)
        serial_number_norm = normalize_serial(serial_number)
        logger.info(f"Normalized serial to search: {serial_number_norm}")
        
        # Check if serial number exists in the Excel file (normalized)
        matching_rows = df[df['serial_normalized'] == serial_number_norm]
        result = len(matching_rows) > 0
        logger.info(f"Exact serial number match found: {result}")
        
        # If exact match found, return it
        if result:
            product_name = None
            product_description = None
            
            if product_name_column and product_name_column in matching_rows.columns:
                product_name = matching_rows.iloc[0][product_name_column]
            
            if product_desc_column and product_desc_column in matching_rows.columns:
                product_description = matching_rows.iloc[0][product_desc_column]
            
            return True, product_name, product_description
        
        # If no exact match, try fuzzy matching for OCR errors
        logger.info("Attempting fuzzy matching for potential OCR errors...")
        
        # Get all normalized serials for comparison
        all_serials = df['serial_normalized'].tolist()
        
        # Try to find close matches (1-2 character differences)
        from difflib import SequenceMatcher
        
        best_match = None
        best_similarity = 0.0
        min_similarity_threshold = 0.85  # 85% similarity required
        
        for excel_serial in all_serials:
            if not excel_serial or len(excel_serial) < 6:
                continue
                
            # Calculate similarity
            similarity = SequenceMatcher(None, serial_number_norm, excel_serial).ratio()
            
            # Also check if one contains the other (for missing characters)
            if (serial_number_norm in excel_serial or excel_serial in serial_number_norm) and len(excel_serial) >= 8:
                similarity = max(similarity, 0.9)
            
            if similarity > best_similarity and similarity >= min_similarity_threshold:
                best_similarity = similarity
                best_match = excel_serial
        
        if best_match:
            logger.info(f"Found fuzzy match: {best_match} (similarity: {best_similarity:.2f})")
            fuzzy_rows = df[df['serial_normalized'] == best_match]
            
            if len(fuzzy_rows) > 0:
                product_name = None
                product_description = None
                
                if product_name_column and product_name_column in fuzzy_rows.columns:
                    product_name = fuzzy_rows.iloc[0][product_name_column]
                
                if product_desc_column and product_desc_column in fuzzy_rows.columns:
                    product_description = fuzzy_rows.iloc[0][product_desc_column]
                
                return True, product_name, product_description
        
        logger.info("No exact or fuzzy match found")
        return False, None, None
        
    except Exception as e:
        logger.error(f"Error checking serial number: {str(e)}")
        traceback.print_exc()
        return False, None, None

# Enhanced OCR function
def extract_serial_from_image(image_file):
    """Extract serial number from image using enhanced OCR"""
    try:
        # Try to use enhanced OCR first
        from enhanced_ocr import enhanced_ocr
        return enhanced_ocr.extract_serial_number(image_file)
    except ImportError:
        # Fallback to basic OCR if enhanced not available
        logger.warning("Enhanced OCR not available, using basic OCR")
        return basic_extract_serial_from_image(image_file)

def basic_extract_serial_from_image(image_file):
    """Fallback basic OCR function"""
    if not OCR_AVAILABLE:
        return None, "OCR functionality is not available"
    
    try:
        import cv2
        import numpy as np
        from PIL import Image
        import pytesseract
        
        # Read and process the image
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            return None, "Could not read image file"
        
        # Basic preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_image = Image.fromarray(thresh)
        
        # Extract text
        text = pytesseract.image_to_string(pil_image, config='--psm 6')
        
        if not text.strip():
            return None, "No text found in image"
        
        # Basic corrections
        corrected_text = text.upper()
        if corrected_text.startswith('S'):
            corrected_text = '5' + corrected_text[1:]
        
        corrected_text = re.sub(r'KRW2', 'KRWZ', corrected_text)
        cleaned_text = re.sub(r'[^A-Z0-9]', '', corrected_text)
        
        # Pattern matching
        patterns = [
            r'[0-9]{3}[A-Z]{2}[0-9A-Z]{5,8}',
            r'[0-9]{2,4}[A-Z0-9]{6,12}',
            r'[A-Z0-9]{8,15}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, cleaned_text)
            if matches:
                return max(matches, key=len), f"Extracted from text: {text.strip()}"
        
        return None, f"Could not identify serial number in text: {text.strip()}"
        
    except Exception as e:
        logger.error(f"Error during basic OCR: {str(e)}")
        return None, f"Error processing image: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

@app.route('/check_serial', methods=['POST'])
def check_serial():
    """Check serial number manually entered by user"""
    serial_number = request.form.get('serial_number')
    excel_url = os.getenv('EXCEL_URL')
    lang = request.form.get('lang', 'en')
    
    if not excel_url:
        return jsonify({'error': get_message('error_excel', lang)}), 400
    
    if not serial_number or not serial_number.strip():
        return jsonify({'error': 'Please enter a serial number'}), 400
    
    logger.info(f"Checking serial number: {serial_number}")
    is_valid, product_name, product_description = check_serial_in_excel(serial_number.strip(), excel_url)
    
    response_data = {
        'valid': is_valid,
        'message': get_message('success' if is_valid else 'not_found', lang),
        'serial_number': serial_number.strip()
    }
    
    if is_valid:
        response_data['product_name'] = product_name
        response_data['product_description'] = product_description
    
    return jsonify(response_data)

@app.route('/upload_serial_image', methods=['POST'])
def upload_serial_image():
    """Extract serial number from uploaded image"""
    if 'serial_image' not in request.files:
        lang = request.form.get('lang', 'en')
        return jsonify({'error': get_message('error_file', lang)}), 400
    
    file = request.files['serial_image']
    excel_url = os.getenv('EXCEL_URL')
    lang = request.form.get('lang', 'en')
    
    if not excel_url:
        return jsonify({'error': get_message('error_excel', lang)}), 400
    
    if not file or file.filename == '':
        return jsonify({'error': get_message('error_file', lang)}), 400
    
    # Try to extract serial number from image
    serial_number, extraction_info = extract_serial_from_image(file)
    
    if not serial_number:
        return jsonify({
            'error': get_message('error_ocr', lang),
            'extracted_text': extraction_info or 'Could not process image'
        }), 400
    
    # Check the extracted serial number
    is_valid, product_name, product_description = check_serial_in_excel(serial_number, excel_url)
    
    response_data = {
        'serial_number': serial_number,
        'valid': is_valid,
        'message': get_message('success' if is_valid else 'not_found', lang),
        'extracted_text': extraction_info or ''
    }
    
    if is_valid:
        response_data['product_name'] = product_name
        response_data['product_description'] = product_description
    
    return jsonify(response_data)

if __name__ == '__main__':
    # Use environment variables for host and port if available
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting Flask app on port {port}")
    logger.info(f"OCR Available: {OCR_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 