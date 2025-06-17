# Excel to PowerPoint Converter

A simple web application that converts Excel files to PowerPoint presentations. The application creates a PowerPoint presentation with a title slide and a data table containing the Excel data.

## Features

- Upload Excel (.xlsx) files
- Automatic conversion to PowerPoint
- Clean and modern web interface
- Maximum file size: 16MB

## Setup

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Click the "Choose File" button to select an Excel file
2. Click "Convert to PowerPoint" to process the file
3. The PowerPoint file will be automatically downloaded

## Requirements

- Python 3.7 or higher
- Flask
- pandas
- openpyxl
- python-pptx

## Notes

- The application creates an 'uploads' directory to temporarily store files
- Excel files are automatically deleted after conversion
- The PowerPoint presentation includes a title slide and a data table 