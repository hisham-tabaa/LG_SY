// Language management
let currentLanguage = 'en';

// Translations for messages
const translations = {
    en: {
        success: 'This product is from LG Syria',
        notFound: 'Product not found',
        enterSerial: 'Please enter a serial number',
        selectImage: 'Please select an image of the serial number',
        processingError: 'Failed to process image',
        verifyError: 'Failed to verify serial number',
        takePicture: 'Take Picture',
        useCamera: 'Use Camera'
    },
    ar: {
        success: 'هذا المنتج من إل جي سوريا',
        notFound: 'المنتج غير موجود',
        enterSerial: 'الرجاء إدخال الرقم التسلسلي',
        selectImage: 'الرجاء اختيار صورة للرقم التسلسلي',
        processingError: 'فشل في معالجة الصورة',
        verifyError: 'فشل في التحقق من الرقم التسلسلي',
        takePicture: 'التقاط صورة',
        useCamera: 'استخدام الكاميرا'
    }
};

// Change language function
function changeLanguage(lang) {
    currentLanguage = lang;
    
    // Update HTML direction
    if (lang === 'ar') {
        document.documentElement.setAttribute('dir', 'rtl');
        document.body.classList.add('rtl');
    } else {
        document.documentElement.setAttribute('dir', 'ltr');
        document.body.classList.remove('rtl');
    }
    
    // Update language buttons
    document.querySelectorAll('.language-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.language-btn[onclick="changeLanguage('${lang}')"]`).classList.add('active');
    
    // Show/hide language-specific elements
    document.querySelectorAll('.lang-en, .lang-ar').forEach(el => {
        el.style.display = 'none';
    });
    document.querySelectorAll(`.lang-${lang}`).forEach(el => {
        el.style.display = '';
    });
    
    // Update placeholder text
    if (lang === 'ar') {
        document.getElementById('serialNumber').placeholder = 'أدخل الرقم التسلسلي للمنتج';
    } else {
        document.getElementById('serialNumber').placeholder = 'Enter product serial number';
    }
    
    // Update camera button text if it exists
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.textContent = translations[lang].useCamera;
    }
}

// Show loading spinner
function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('resultContainer').classList.add('d-none');
    document.getElementById('productDetails').classList.add('d-none');
}

// Hide loading spinner
function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

// Display result message
function showResult(message, isSuccess, extraInfo = null, productData = null) {
    const resultContainer = document.getElementById('resultContainer');
    const resultMessage = document.getElementById('resultMessage');
    const extractedInfo = document.getElementById('extractedInfo');
    const productDetails = document.getElementById('productDetails');
    
    resultContainer.classList.remove('d-none');
    resultMessage.textContent = message;
    resultMessage.className = 'alert ' + (isSuccess ? 'alert-success' : 'alert-danger');
    
    // Show extracted info if available
    if (extraInfo) {
        extractedInfo.textContent = extraInfo;
        extractedInfo.classList.remove('d-none');
    } else {
        extractedInfo.classList.add('d-none');
    }
    
    // Show product details if available
    if (productData && isSuccess) {
        document.getElementById('productSerial').textContent = productData.serial || '';
        document.getElementById('productName').textContent = productData.name || '';
        document.getElementById('productDescription').textContent = productData.description || '';
        productDetails.classList.remove('d-none');
    } else {
        productDetails.classList.add('d-none');
    }
}

// Handle manual serial number check
async function checkSerial() {
    const serialNumber = document.getElementById('serialNumber').value.trim();
    
    if (!serialNumber) {
        showResult(translations[currentLanguage].enterSerial, false);
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('serial_number', serialNumber);
        formData.append('lang', currentLanguage);

        const response = await fetch('/check_serial', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            showResult(
                data.message, 
                data.valid, 
                null, 
                data.valid ? {
                    serial: data.serial_number,
                    name: data.product_name,
                    description: data.product_description
                } : null
            );
        } else {
            showResult(data.error || translations[currentLanguage].verifyError, false);
        }
    } catch (error) {
        showResult(translations[currentLanguage].verifyError, false);
    } finally {
        hideLoading();
    }
}

// Handle image capture from camera
function setupCameraCapture() {
    const fileInput = document.getElementById('serialImage');
    const cameraBtn = document.getElementById('cameraBtn');
    
    if (!cameraBtn) return;
    
    cameraBtn.addEventListener('click', function() {
        // Set capture attribute to camera to force using the camera
        fileInput.setAttribute('capture', 'environment');
        fileInput.click();
        
        // Remove the capture attribute after clicking to allow gallery selection next time
        setTimeout(() => {
            fileInput.removeAttribute('capture');
        }, 1000);
    });
}

// Handle serial number image upload
async function uploadSerialImage() {
    const fileInput = document.getElementById('serialImage');
    const file = fileInput.files[0];

    if (!file) {
        showResult(translations[currentLanguage].selectImage, false);
        return;
    }

    // Show information about image processing
    showLoading();

    try {
        const formData = new FormData();
        formData.append('serial_image', file);
        formData.append('lang', currentLanguage);

        const response = await fetch('/upload_serial_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            let extraInfo = null;
            if (data.serial_number) {
                extraInfo = currentLanguage === 'en' ? 
                    `✓ Extracted serial number: ${data.serial_number}` : 
                    `✓ الرقم التسلسلي المستخرج: ${data.serial_number}`;
                    
                if (data.extracted_text) {
                    extraInfo += currentLanguage === 'en' ? 
                        `\nExtracted text: ${data.extracted_text}` : 
                        `\nالنص المستخرج: ${data.extracted_text}`;
                }
            }
            
            showResult(
                data.message, 
                data.valid, 
                extraInfo, 
                data.valid ? {
                    serial: data.serial_number,
                    name: data.product_name,
                    description: data.product_description
                } : null
            );
        } else {
            let errorMsg = data.error || translations[currentLanguage].processingError;
            let extraInfo = null;
            
            if (data.extracted_text) {
                extraInfo = currentLanguage === 'en' ? 
                    `Extracted text: ${data.extracted_text}\n\n⚠️ Could not identify a valid serial number from this text.\nTip: Try entering the serial number manually for best results.` : 
                    `النص المستخرج: ${data.extracted_text}\n\n⚠️ لم نتمكن من تحديد رقم تسلسلي صالح من هذا النص.\nنصيحة: جرب إدخال الرقم التسلسلي يدوياً للحصول على أفضل النتائج.`;
            } else {
                // Provide helpful guidance when OCR fails completely
                extraInfo = currentLanguage === 'en' ? 
                    `💡 Image processing tip:\n• Make sure the serial number is clearly visible\n• Ensure good lighting\n• Try taking a closer photo\n• For best results, enter the serial number manually` : 
                    `💡 نصائح لمعالجة الصور:\n• تأكد من وضوح الرقم التسلسلي\n• تأكد من الإضاءة الجيدة\n• جرب التقاط صورة أقرب\n• للحصول على أفضل النتائج، أدخل الرقم التسلسلي يدوياً`;
            }
            
            showResult(errorMsg, false, extraInfo);
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        const errorMsg = currentLanguage === 'en' ? 
            'Failed to process image. Please try again or enter the serial number manually.' :
            'فشل في معالجة الصورة. يرجى المحاولة مرة أخرى أو إدخال الرقم التسلسلي يدوياً.';
        
        const tipMsg = currentLanguage === 'en' ? 
            '💡 For fastest and most accurate results, we recommend entering the serial number manually above.' :
            '💡 للحصول على أسرع وأدق النتائج، نوصي بإدخال الرقم التسلسلي يدوياً أعلاه.';
            
        showResult(errorMsg, false, tipMsg);
    } finally {
        hideLoading();
        fileInput.value = ''; // Clear the file input
    }
}

// Add enter key support for serial number input
document.getElementById('serialNumber').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        checkSerial();
    }
});

// Initialize language and camera functionality on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if browser language is Arabic
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang.startsWith('ar')) {
        changeLanguage('ar');
    } else {
        changeLanguage('en');
    }
    
    // Setup camera capture
    setupCameraCapture();
}); 