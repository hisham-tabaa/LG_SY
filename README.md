# LG Syria Product Verification System

This web application allows users to verify LG products by either entering a serial number manually or uploading an image of the serial number. The system checks the provided serial number against an online Excel database to verify if the product is from LG Syria and displays product details if found.

## Features

- Manual serial number verification
- Serial number image recognition using OCR
- Direct camera capture for mobile devices
- Real-time verification against online Excel database
- Product details display (name and description)
- Modern and responsive UI with LG branding
- Bilingual support (English and Arabic)
- Loading indicators and error handling

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A web browser
- Camera (for serial number image capture)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Configure the environment:
- Rename `.env.example` to `.env`
- Update the `EXCEL_URL` in `.env` with your Excel file URL

5. Make sure the logo is placed in the correct location:
- Place the logo file at `static/uploads/MES Logo (1).png`

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. You can verify products in three ways:
   - Enter the serial number manually in the input field
   - Upload an image of the serial number from your gallery
   - Take a photo directly using the "Use Camera" button on mobile devices

4. Switch between English and Arabic using the language selector in the top right corner

## Excel File Format

The Excel file should have three columns:
1. **Serial Number Column**: Contains product serial numbers (named 'SerialNumber', 'serial_number', 'serial', etc.)
2. **Product Name Column**: Contains product names (named 'product_name', 'name', 'productname', etc.)
3. **Product Description Column**: Contains product descriptions (named 'description', 'product_description', etc.)

Example Excel file structure:
| SerialNumber | Product Name | Product Description |
|--------------|--------------|---------------------|
| S4NW24K23WE.EC6GJOR | مكيف ابيض 2 طن (داخلية) | Split Air Conditioner 24K |
| DFC513FV.APYPMEA | حلاجة فضية وبراد-ماء | Refrigerator with Water Dispenser |

## Development

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python Flask
- Dependencies: See requirements.txt

## Troubleshooting

1. If OCR fails to extract the serial number:
   - Ensure the image is clear and high-contrast
   - Make sure the text is horizontal and not skewed
   - Try taking the photo in better lighting conditions
   - Hold the camera steady when taking the photo

2. If camera capture doesn't work:
   - Make sure you've granted camera permissions to the website
   - Try using a different browser if issues persist
   - On some devices, you may need to use the gallery upload instead

3. If serial verification fails:
   - Check your internet connection
   - Verify the Excel file URL is accessible
   - Ensure the serial number format matches the database

## License

[Your License Here]

## Support

For support, please contact [Your Contact Information] 