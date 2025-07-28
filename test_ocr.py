#!/usr/bin/env python3
"""
Quick test to verify Tesseract OCR installation
Run this after installing Tesseract: python test_ocr.py
"""

def test_tesseract():
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract command found!")
            print(f"   Version: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
            return True
        else:
            print("❌ Tesseract command failed")
            return False
    except:
        print("❌ Tesseract not found - make sure 'Add to PATH' was checked during installation")
        return False

def test_pytesseract():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ pytesseract can access Tesseract")
        return True
    except:
        print("❌ pytesseract cannot access Tesseract")
        return False

def test_opencv():
    try:
        import cv2
        print("✅ OpenCV available")
        return True
    except:
        print("❌ OpenCV not found")
        return False

if __name__ == "__main__":
    print("🔍 Testing OCR Installation")
    print("=" * 30)
    
    tests = [test_tesseract, test_pytesseract, test_opencv]
    results = [test() for test in tests]
    
    print("=" * 30)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("Your Flask app should now support image upload!")
        print("\nRestart your Flask app: python app.py")
    else:
        print("⚠️ Some tests failed.")
        print("Please reinstall Tesseract and check 'Add to PATH'") 