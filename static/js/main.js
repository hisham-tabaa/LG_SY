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
function showResult(message, isSuccess) {
    const resultContainer = document.getElementById('resultContainer');
    const resultMessage = document.getElementById('resultMessage');
    
    resultContainer.classList.remove('d-none');
    resultMessage.textContent = message;
    resultMessage.className = 'alert ' + (isSuccess ? 'alert-success' : 'alert-danger');
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
            showResult(data.message, data.valid);
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