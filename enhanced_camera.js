/**
 * Enhanced Camera Functionality for Serial Number Capture
 */

class EnhancedCamera {
    constructor() {
        this.stream = null;
        this.video = null;
        this.canvas = null;
        this.isStreaming = false;
        this.constraints = {
            video: {
                facingMode: 'environment', // Use back camera on mobile
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };
    }

    async initialize() {
        try {
            // Check if camera is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera not supported by browser');
            }

            // Create camera modal elements
            this.createCameraModal();
            this.setupEventListeners();
            
            return true;
        } catch (error) {
            console.error('Camera initialization failed:', error);
            return false;
        }
    }

    createCameraModal() {
        const modalHTML = `
            <div id="cameraModal" class="modal fade" tabindex="-1" role="dialog">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <span class="lang-en">Capture Serial Number</span>
                                <span class="lang-ar" style="display: none;">التقاط الرقم التسلسلي</span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div id="cameraContainer" class="position-relative">
                                <video id="cameraVideo" class="w-100 rounded" autoplay muted playsinline></video>
                                <canvas id="cameraCanvas" class="d-none"></canvas>
                                
                                <!-- Camera overlay for guidance -->
                                <div id="cameraOverlay" class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center">
                                    <div class="border border-primary border-3 rounded" style="width: 80%; height: 60%; background: rgba(255,255,255,0.1);">
                                        <div class="text-center mt-2">
                                            <small class="text-primary lang-en">Position serial number here</small>
                                            <small class="text-primary lang-ar" style="display: none;">ضع الرقم التسلسلي هنا</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Camera controls -->
                            <div class="mt-3">
                                <button id="captureBtn" class="btn btn-primary btn-lg me-2">
                                    <i class="bi bi-camera"></i>
                                    <span class="lang-en">Capture</span>
                                    <span class="lang-ar" style="display: none;">التقاط</span>
                                </button>
                                <button id="switchCameraBtn" class="btn btn-secondary me-2">
                                    <i class="bi bi-arrow-repeat"></i>
                                    <span class="lang-en">Switch</span>
                                    <span class="lang-ar" style="display: none;">تبديل</span>
                                </button>
                                <button id="retakeBtn" class="btn btn-outline-secondary d-none">
                                    <i class="bi bi-arrow-clockwise"></i>
                                    <span class="lang-en">Retake</span>
                                    <span class="lang-ar" style="display: none;">إعادة التقاط</span>
                                </button>
                            </div>
                            
                            <!-- Preview captured image -->
                            <div id="capturedImageContainer" class="mt-3 d-none">
                                <img id="capturedImage" class="img-fluid rounded" style="max-height: 300px;">
                                <div class="mt-2">
                                    <button id="useCapturedBtn" class="btn btn-success">
                                        <i class="bi bi-check-circle"></i>
                                        <span class="lang-en">Use This Image</span>
                                        <span class="lang-ar" style="display: none;">استخدام هذه الصورة</span>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Status messages -->
                            <div id="cameraStatus" class="mt-3">
                                <div class="spinner-border d-none" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <div id="cameraMessage" class="text-muted"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page if not exists
        if (!document.getElementById('cameraModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        // Get references
        this.modal = document.getElementById('cameraModal');
        this.video = document.getElementById('cameraVideo');
        this.canvas = document.getElementById('cameraCanvas');
    }

    setupEventListeners() {
        const captureBtn = document.getElementById('captureBtn');
        const switchCameraBtn = document.getElementById('switchCameraBtn');
        const retakeBtn = document.getElementById('retakeBtn');
        const useCapturedBtn = document.getElementById('useCapturedBtn');

        captureBtn?.addEventListener('click', () => this.captureImage());
        switchCameraBtn?.addEventListener('click', () => this.switchCamera());
        retakeBtn?.addEventListener('click', () => this.retake());
        useCapturedBtn?.addEventListener('click', () => this.useCapturedImage());

        // Modal events
        this.modal?.addEventListener('shown.bs.modal', () => this.startCamera());
        this.modal?.addEventListener('hidden.bs.modal', () => this.stopCamera());
    }

    async startCamera() {
        try {
            this.showStatus('Starting camera...', 'بدء تشغيل الكاميرا...');
            
            this.stream = await navigator.mediaDevices.getUserMedia(this.constraints);
            this.video.srcObject = this.stream;
            
            this.video.addEventListener('loadedmetadata', () => {
                this.isStreaming = true;
                this.hideStatus();
                
                // Setup canvas dimensions
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
            });

        } catch (error) {
            console.error('Camera start failed:', error);
            this.showStatus(
                'Camera not available. Please check permissions.',
                'الكاميرا غير متاحة. يرجى التحقق من الصلاحيات.'
            );
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isStreaming = false;
        this.resetUI();
    }

    async switchCamera() {
        if (!this.isStreaming) return;

        // Toggle between front and back camera
        const currentFacing = this.constraints.video.facingMode;
        this.constraints.video.facingMode = currentFacing === 'environment' ? 'user' : 'environment';

        this.stopCamera();
        await this.startCamera();
    }

    captureImage() {
        if (!this.isStreaming) return;

        const context = this.canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

        // Convert to blob and display
        this.canvas.toBlob((blob) => {
            const imageUrl = URL.createObjectURL(blob);
            this.displayCapturedImage(imageUrl, blob);
        }, 'image/jpeg', 0.8);
    }

    displayCapturedImage(imageUrl, blob) {
        const capturedImage = document.getElementById('capturedImage');
        const container = document.getElementById('capturedImageContainer');
        const captureBtn = document.getElementById('captureBtn');
        const retakeBtn = document.getElementById('retakeBtn');

        capturedImage.src = imageUrl;
        container.classList.remove('d-none');
        captureBtn.classList.add('d-none');
        retakeBtn.classList.remove('d-none');

        // Store blob for upload
        this.capturedBlob = blob;
    }

    retake() {
        const container = document.getElementById('capturedImageContainer');
        const captureBtn = document.getElementById('captureBtn');
        const retakeBtn = document.getElementById('retakeBtn');

        container.classList.add('d-none');
        captureBtn.classList.remove('d-none');
        retakeBtn.classList.add('d-none');

        this.capturedBlob = null;
    }

    async useCapturedImage() {
        if (!this.capturedBlob) return;

        // Close modal
        const modal = bootstrap.Modal.getInstance(this.modal);
        modal.hide();

        // Create FormData and upload
        const formData = new FormData();
        formData.append('serial_image', this.capturedBlob, 'camera_capture.jpg');
        formData.append('lang', currentLanguage);

        // Show loading and process
        showLoading();
        
        try {
            const response = await fetch('/upload_serial_image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                // Format product information
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
                
                // Add product details if available
                let productInfo = null;
                if (data.valid) {
                    productInfo = {
                        serial: data.serial_number,
                        name: data.product_name || 'N/A',
                        description: data.product_description || 'N/A'
                    };
                    
                    if (data.product_name || data.product_description) {
                        const productDetails = currentLanguage === 'en' ? 
                            `\n📋 Product Details:\n• Name: ${data.product_name || 'N/A'}\n• Code: ${data.product_description || 'N/A'}` :
                            `\n📋 تفاصيل المنتج:\n• الاسم: ${data.product_name || 'غير متوفر'}\n• الكود: ${data.product_description || 'غير متوفر'}`;
                        extraInfo = (extraInfo || '') + productDetails;
                    }
                }
                
                showResult(data.message, data.valid, extraInfo, productInfo);
            } else {
                let errorMsg = data.error || 'Processing failed';
                let extraInfo = null;
                
                if (data.extracted_text) {
                    extraInfo = currentLanguage === 'en' ? 
                        `Extracted text: ${data.extracted_text}\n\n⚠️ Could not identify serial number.\nTip: Try manual entry for best results.` : 
                        `النص المستخرج: ${data.extracted_text}\n\n⚠️ لم نتمكن من تحديد رقم تسلسلي.\nنصيحة: جرب الإدخال اليدوي للحصول على أفضل النتائج.`;
                }
                
                showResult(errorMsg, false, extraInfo);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            const errorMsg = currentLanguage === 'en' ? 
                'Failed to process camera image. Please try again.' :
                'فشل في معالجة صورة الكاميرا. يرجى المحاولة مرة أخرى.';
            showResult(errorMsg, false);
        } finally {
            hideLoading();
        }
    }

    resetUI() {
        const elements = [
            'capturedImageContainer',
            'retakeBtn'
        ];
        
        elements.forEach(id => {
            document.getElementById(id)?.classList.add('d-none');
        });
        
        const showElements = [
            'captureBtn'
        ];
        
        showElements.forEach(id => {
            document.getElementById(id)?.classList.remove('d-none');
        });
    }

    showStatus(enText, arText) {
        const statusEl = document.getElementById('cameraStatus');
        const messageEl = document.getElementById('cameraMessage');
        const spinner = statusEl.querySelector('.spinner-border');
        
        spinner.classList.remove('d-none');
        messageEl.textContent = currentLanguage === 'en' ? enText : arText;
    }

    hideStatus() {
        const statusEl = document.getElementById('cameraStatus');
        const spinner = statusEl.querySelector('.spinner-border');
        const messageEl = document.getElementById('cameraMessage');
        
        spinner.classList.add('d-none');
        messageEl.textContent = '';
    }

    // Public method to open camera
    open() {
        const modal = new bootstrap.Modal(this.modal);
        modal.show();
    }
}

// Initialize enhanced camera
let enhancedCamera = null;

document.addEventListener('DOMContentLoaded', async function() {
    enhancedCamera = new EnhancedCamera();
    const initialized = await enhancedCamera.initialize();
    
    if (initialized) {
        console.log('Enhanced camera initialized successfully');
    } else {
        console.warn('Enhanced camera initialization failed');
    }
});

// Export for global use
window.openEnhancedCamera = function() {
    if (enhancedCamera) {
        enhancedCamera.open();
    } else {
        alert(currentLanguage === 'en' ? 
            'Camera not available' : 
            'الكاميرا غير متاحة'
        );
    }
}; 