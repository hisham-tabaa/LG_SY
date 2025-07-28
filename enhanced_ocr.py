"""
Enhanced OCR module with multiple engines and advanced image preprocessing
"""

import cv2
import numpy as np
import logging
from PIL import Image, ImageEnhance, ImageFilter
import re

logger = logging.getLogger(__name__)

class EnhancedOCR:
    def __init__(self):
        self.easyocr_reader = None
        self.tesseract_available = False
        
        # Initialize EasyOCR
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['en', 'ar'], gpu=False)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {str(e)}")
        
        # Check Tesseract
        try:
            import pytesseract
            import subprocess
            result = subprocess.run(['tesseract', '--version'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   check=False, timeout=5)
            self.tesseract_available = result.returncode == 0
            if self.tesseract_available:
                logger.info("Tesseract OCR available as backup")
        except:
            logger.warning("Tesseract OCR not available")
    
    def preprocess_image(self, image):
        """Advanced image preprocessing for better OCR results"""
        try:
            # Convert to numpy array if PIL
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            original = image.copy()
            
            # 1. Resize if too small (OCR works better on larger images)
            height, width = image.shape[:2]
            if min(height, width) < 300:
                scale = 300 / min(height, width)
                image = cv2.resize(image, (int(width * scale), int(height * scale)), 
                                 interpolation=cv2.INTER_CUBIC)
                logger.info(f"Upscaled image from {width}x{height} to {image.shape[1]}x{image.shape[0]}")
            
            # 2. Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 3. Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 4. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 5. Multiple threshold approaches
            processed_images = []
            
            # Otsu thresholding
            _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(("otsu", otsu))
            
            # Adaptive thresholding
            adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            processed_images.append(("adaptive", adaptive))
            
            # Mean thresholding (good for uniform lighting)
            mean_val = np.mean(enhanced)
            _, mean_thresh = cv2.threshold(enhanced, mean_val, 255, cv2.THRESH_BINARY)
            processed_images.append(("mean", mean_thresh))
            
            return processed_images
            
        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            return [("original", image)]
    
    def extract_text_easyocr(self, image):
        """Extract text using EasyOCR"""
        if not self.easyocr_reader:
            return None
        
        try:
            # EasyOCR expects RGB format
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
            results = self.easyocr_reader.readtext(rgb_image, detail=0)
            text = ' '.join(results) if results else ''
            
            if text.strip():
                logger.info(f"EasyOCR extracted: {text.strip()}")
                return text.strip()
            
        except Exception as e:
            logger.error(f"EasyOCR error: {str(e)}")
        
        return None
    
    def extract_text_tesseract(self, image):
        """Extract text using Tesseract as backup"""
        if not self.tesseract_available:
            return None
        
        try:
            import pytesseract
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image) if isinstance(image, np.ndarray) else image
            
            # Try multiple PSM configurations
            configs = [
                '--psm 8 --oem 3',  # Single word
                '--psm 7 --oem 3',  # Single text line
                '--psm 6 --oem 3',  # Uniform block
                '--psm 13 --oem 3', # Raw line
            ]
            
            best_text = ""
            for config in configs:
                try:
                    text = pytesseract.image_to_string(pil_image, config=config)
                    if text and len(text.strip()) > len(best_text):
                        best_text = text.strip()
                except:
                    continue
            
            if best_text:
                logger.info(f"Tesseract extracted: {best_text}")
                return best_text
                
        except Exception as e:
            logger.error(f"Tesseract error: {str(e)}")
        
        return None
    
    def extract_serial_number(self, image_file):
        """Main function to extract serial number from image"""
        try:
            # Read image
            file_bytes = np.frombuffer(image_file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                return None, "Could not read image file"
            
            logger.info(f"Processing image of size: {image.shape}")
            
            # Preprocess image
            processed_images = self.preprocess_image(image)
            
            all_texts = []
            
            # Try EasyOCR on all processed images
            if self.easyocr_reader:
                for name, proc_img in processed_images:
                    text = self.extract_text_easyocr(proc_img)
                    if text:
                        all_texts.append(f"EasyOCR ({name}): {text}")
            
            # Try Tesseract as backup
            if self.tesseract_available:
                for name, proc_img in processed_images:
                    text = self.extract_text_tesseract(proc_img)
                    if text:
                        all_texts.append(f"Tesseract ({name}): {text}")
            
            logger.info(f"All extracted texts: {all_texts}")
            
            # Find the best serial number from all texts
            best_serial = None
            best_confidence = 0
            
            for text_info in all_texts:
                text = text_info.split(': ', 1)[-1]  # Remove engine prefix
                serial = self.extract_serial_from_text(text)
                if serial:
                    confidence = self.calculate_serial_confidence(serial)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_serial = serial
            
            if best_serial:
                return best_serial, f"Extracted from multiple OCR engines. Best match: {best_serial}"
            
            # Return all texts for debugging
            combined_text = '\n'.join(all_texts) if all_texts else "No text detected"
            return None, f"Could not identify serial number. Extracted texts:\n{combined_text}"
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return None, f"Error processing image: {str(e)}"
    
    def extract_serial_from_text(self, text):
        """Extract serial number from text with enhanced patterns"""
        if not text:
            return None
        
        # Apply OCR corrections
        corrected_text = text.upper()
        if corrected_text.startswith('S'):
            corrected_text = '5' + corrected_text[1:]
        
        # Common OCR corrections
        corrections = {'O': '0', 'I': '1', 'B': '8', 'S': '5'}
        for mistake, fix in corrections.items():
            corrected_text = corrected_text.replace(mistake, fix)
        
        # Fix specific patterns
        corrected_text = re.sub(r'KRW2', 'KRWZ', corrected_text)
        corrected_text = re.sub(r'([A-Z]{2,3})2([0-9]{4,})', r'\1Z\2', corrected_text)
        
        logger.info(f"Text after corrections: {corrected_text}")
        
        # Clean text
        cleaned_text = re.sub(r'[^A-Z0-9]', '', corrected_text)
        
        # Enhanced patterns (most specific first)
        patterns = [
            r'[0-9]{3}[A-Z]{2}[0-9A-Z]{5,8}',    # 505KRWZ35633
            r'[0-9]{2,4}[A-Z0-9]{6,12}',         # General number-first
            r'[A-Z]{2,3}[0-9A-Z]{5,12}',         # Letter-first
            r'LG[0-9A-Z]{5,12}',                 # LG products
            r'[0-9][A-Z0-9]{7,14}',              # Number-first patterns
            r'[A-Z0-9]{8,15}'                    # General alphanumeric
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, cleaned_text)
            if matches:
                best = max(matches, key=len)
                logger.info(f"Found serial with pattern {pattern}: {best}")
                return best
        
        return None
    
    def calculate_serial_confidence(self, serial):
        """Calculate confidence score for extracted serial number"""
        if not serial:
            return 0
        
        score = 0
        
        # Length scoring (typical serial numbers are 8-15 chars)
        if 8 <= len(serial) <= 15:
            score += 30
        elif 6 <= len(serial) <= 17:
            score += 20
        
        # Pattern scoring
        if re.match(r'[0-9]{3}[A-Z]{2}[0-9A-Z]{5,8}', serial):  # 505KRWZ35633 pattern
            score += 40
        elif re.match(r'[0-9]{2,4}[A-Z0-9]{6,12}', serial):
            score += 30
        elif re.match(r'[A-Z0-9]{8,15}', serial):
            score += 20
        
        # Mixed alphanumeric gets bonus
        has_letters = bool(re.search(r'[A-Z]', serial))
        has_numbers = bool(re.search(r'[0-9]', serial))
        if has_letters and has_numbers:
            score += 20
        
        # Specific pattern bonuses
        if 'KRW' in serial:
            score += 10
        if serial.startswith(('5', '1', '2', '3', '4')):  # Common number prefixes
            score += 5
        
        return min(score, 100)  # Cap at 100

# Global instance
enhanced_ocr = EnhancedOCR() 