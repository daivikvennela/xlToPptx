import uuid
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os
from werkzeug.utils import secure_filename
import json
import logging
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CHUNK_SIZE = 15  # Number of rows per slide

def extract_excel_content(excel_file):
    """Extract and organize content from Excel file."""
    # Read all sheets from the Excel file
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    content = {
        'sheets': [],
        'summary': {
            'total_sheets': len(excel_data),
            'total_rows': 0,
            'total_columns': 0
        },
        'slides': []  # For preview
    }
    
    for sheet_name, df in excel_data.items():
        # Replace NaN, NaT, and inf with None for JSON serialization
        df_clean = df.where(pd.notnull(df), None)
        df_clean = df_clean.replace({pd.NaT: None, np.datetime64('NaT'): None})
        sheet_content = {
            'name': sheet_name,
            'columns': df_clean.columns.tolist(),
            'data': df_clean.values.tolist(),
            'rows': len(df_clean),
            'columns_count': len(df_clean.columns),
            'has_numeric': any(df_clean.select_dtypes(include=['number']).columns),
            'has_text': any(df_clean.select_dtypes(include=['object']).columns)
        }
        
        # Add summary statistics for numeric columns
        numeric_cols = df_clean.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats = df_clean[numeric_cols].describe().to_dict()
            # Replace NaN/inf in stats with None
            for col, stat_dict in stats.items():
                for k, v in stat_dict.items():
                    if pd.isnull(v) or v in [float('inf'), float('-inf')]:
                        stat_dict[k] = None
            sheet_content['statistics'] = stats
        
        content['sheets'].append(sheet_content)
        content['summary']['total_rows'] += len(df_clean)
        content['summary']['total_columns'] += len(df_clean.columns)
        # --- Add slide preview structure ---
        # Title slide for each sheet
        content['slides'].append({
            'type': 'title',
            'title': f"Sheet: {sheet_name}",
            'subtitle': f"Rows: {len(df_clean)}, Columns: {len(df_clean.columns)}"
        })
        # Data table slide for each sheet
        content['slides'].append({
            'type': 'table',
            'title': f"Data from {sheet_name}",
            'columns': df_clean.columns.tolist(),
            'data': df_clean.values.tolist()
        })
        # Statistics slide if available
        if 'statistics' in sheet_content:
            content['slides'].append({
                'type': 'statistics',
                'title': f"Statistics for {sheet_name}",
                'statistics': sheet_content['statistics']
            })
    
    return content

def chunk_dataframe(df, chunk_size):
    """Yield successive chunk_size-sized chunks from DataFrame."""
    for start in range(0, len(df), chunk_size):
        yield df.iloc[start:start + chunk_size]

def create_powerpoint_presentation(content, customizations, pptx_file):
    """Create a comprehensive PowerPoint presentation from the Excel content with customizations."""
    prs = Presentation()
    
    # Title Slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = "Excel Data Analysis Report"
    subtitle.text = f"Total Sheets: {content['summary']['total_sheets']}\n" \
                   f"Total Rows: {content['summary']['total_rows']}\n" \
                   f"Total Columns: {content['summary']['total_columns']}"
    
    # Sort customizations by position
    position_order = {'early': 0, 'middle': 1, 'late': 2}
    sorted_customizations = sorted(
        customizations,
        key=lambda x: position_order[x['slidePosition']]
    )
    
    # Process each sheet according to customizations
    for customization in sorted_customizations:
        sheet_name = customization['sheetName']
        slide_type = customization['slideType']
        
        # Find the corresponding sheet data
        sheet_data = next(
            (s for s in content['sheets'] if s['name'] == sheet_name),
            None
        )
        
        if sheet_data:
            if slide_type in ['table', 'both']:
                # Chunk the data and create a slide for each chunk
                for chunk in chunk_dataframe(pd.DataFrame(sheet_data['data'], columns=sheet_data['columns']), CHUNK_SIZE):
                    slide = prs.slides.add_slide(prs.slide_layouts[1])
                    title = slide.shapes.title
                    title.text = f"Data from {sheet_name}"
                    rows = len(chunk) + 1
                    cols = len(chunk.columns)
                    left = Inches(0.5)
                    top = Inches(1.5)
                    width = Inches(9)
                    height = Inches(5)
                    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
                    
                    # Add headers
                    for col, column_name in enumerate(chunk.columns):
                        cell = table.cell(0, col)
                        cell.text = str(column_name)
                        cell.text_frame.paragraphs[0].font.bold = True
                    
                    # Add data
                    for row in range(len(chunk)):
                        for col in range(len(chunk.columns)):
                            cell = table.cell(row + 1, col)
                            cell.text = str(chunk.iloc[row, col])
            
            if slide_type in ['summary', 'both'] and 'statistics' in sheet_data:
                # Add statistics slide
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                title = slide.shapes.title
                title.text = f"Statistics for {sheet_name}"
                
                # Add statistics text
                stats_text = "Statistical Summary:\n\n"
                for col, stats in sheet_data['statistics'].items():
                    stats_text += f"{col}:\n"
                    for stat_name, value in stats.items():
                        stats_text += f"  {stat_name}: {value if value is not None else 'N/A'}\n"
                    stats_text += "\n"
                
                left = Inches(1)
                top = Inches(2)
                width = Inches(8)
                height = Inches(4)
                
                textbox = slide.shapes.add_textbox(left, top, width, height)
                text_frame = textbox.text_frame
                text_frame.text = stats_text
    
    # Save the presentation
    prs.save(pptx_file)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.xlsx'):
        # Generate a unique token for this upload
        file_token = str(uuid.uuid4())
        filename = f"{file_token}_{secure_filename(file.filename)}"
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(excel_path)
        
        try:
            content = extract_excel_content(excel_path)
            # Return the file token so the frontend can use it for generation
            return jsonify({'file_token': file_token, 'content': content, 'slides': content['slides']})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    app.logger.info('Received /generate request data: %s', data)
    if not data or 'customizations' not in data or 'file_token' not in data:
        app.logger.error('Missing customizations or file_token in /generate request: %s', data)
        return jsonify({'error': 'No customization data or file token provided'}), 400
    file_token = data['file_token']
    # Find the file in the uploads folder
    excel_filename = None
    for fname in os.listdir(app.config['UPLOAD_FOLDER']):
        if fname.startswith(file_token + '_'):
            excel_filename = fname
            break
    if not excel_filename:
        app.logger.error('Excel file not found for token: %s', file_token)
        return jsonify({'error': 'Excel file not found'}), 400
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
    pptx_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_token}_presentation.pptx")
    try:
        content = extract_excel_content(excel_path)
        create_powerpoint_presentation(content, data['customizations'], pptx_path)
        app.logger.info('Successfully created PowerPoint for token: %s', file_token)
        return send_file(pptx_path, as_attachment=True)
    except Exception as e:
        app.logger.exception('Error generating PowerPoint: %s', e)
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(pptx_path):
            os.remove(pptx_path)

if __name__ == '__main__':
    app.run(debug=True) 