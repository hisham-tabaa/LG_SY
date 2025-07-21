// Show loading spinner
function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('resultContainer').classList.add('d-none');
}

// Hide loading spinner
function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

// Display result message
function showResult(message, isSuccess, extraInfo = null) {
    const resultContainer = document.getElementById('resultContainer');
    const resultMessage = document.getElementById('resultMessage');
    const extractedInfo = document.getElementById('extractedInfo');
    
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
}

// Handle manual serial number check
async function checkSerial() {
    const serialNumber = document.getElementById('serialNumber').value.trim();
    
    if (!serialNumber) {
        showResult('Please enter a serial number', false);
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('serial_number', serialNumber);

        const response = await fetch('/check_serial', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            showResult(data.message, data.valid);
        } else {
            showResult(data.error || 'An error occurred', false);
        }
    } catch (error) {
        showResult('Failed to verify serial number', false);
    } finally {
        hideLoading();
    }
}

// Handle serial number image upload
async function uploadSerialImage() {
    const fileInput = document.getElementById('serialImage');
    const file = fileInput.files[0];

    if (!file) {
        showResult('Please select an image of the serial number', false);
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('serial_image', file);

        const response = await fetch('/upload_serial_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            let extraInfo = null;
            if (data.serial_number) {
                extraInfo = `Extracted serial number: ${data.serial_number}`;
                if (data.extracted_text) {
                    extraInfo += `\nExtracted text: ${data.extracted_text}`;
                }
            }
            showResult(data.message, data.valid, extraInfo);
        } else {
            let errorMsg = data.error || 'An error occurred';
            let extraInfo = null;
            if (data.extracted_text) {
                extraInfo = `Extracted text: ${data.extracted_text}\n(Could not identify a valid serial number)`;
            }
            showResult(errorMsg, false, extraInfo);
        }
    } catch (error) {
        showResult('Failed to process serial number image', false);
    } finally {
        hideLoading();
        fileInput.value = ''; // Clear the file input
    }
}

// Handle barcode image upload
async function uploadBarcode() {
    const fileInput = document.getElementById('barcodeImage');
    const file = fileInput.files[0];

    if (!file) {
        showResult('Please select a barcode image', false);
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('barcode', file);

        const response = await fetch('/upload_barcode', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            let extraInfo = null;
            if (data.serial_number) {
                extraInfo = `Extracted serial number from barcode: ${data.serial_number}`;
            }
            showResult(data.message, data.valid, extraInfo);
        } else {
            showResult(data.error || 'An error occurred', false);
        }
    } catch (error) {
        showResult('Failed to process barcode image', false);
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