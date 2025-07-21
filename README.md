# LG Syria Product Verification System

This web application allows users to verify LG products by either entering a serial number manually or uploading a barcode image. The system checks the provided serial number against an online Excel database to verify if the product is from LG Syria.

## Features

- Manual serial number verification
- Barcode image upload and processing
- Real-time verification against online Excel database
- Modern and responsive UI
- Loading indicators and error handling

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A web browser
- Camera or barcode scanner (for barcode verification)

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

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. You can verify products in two ways:
   - Enter the serial number manually in the input field
   - Upload a barcode image using the file upload button

## Excel File Format

The Excel file should have a column named 'SerialNumber' containing all valid product serial numbers.

## Development

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python Flask
- Dependencies: See requirements.txt

## Troubleshooting

1. If barcode scanning fails:
   - Ensure the image is clear and well-lit
   - Make sure the barcode is properly focused
   - Try different barcode formats if available

2. If serial verification fails:
   - Check your internet connection
   - Verify the Excel file URL is accessible
   - Ensure the serial number format matches the database

## License

[Your License Here]

## Support

For support, please contact [Your Contact Information] 