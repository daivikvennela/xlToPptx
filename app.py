from flask import Flask, render_template, request, send_file
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_excel_content(excel_file):
    """Extract and organize content from Excel file."""
    # Read all sheets from the Excel file
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    content = {
        'sheets': {},
        'summary': {
            'total_sheets': len(excel_data),
            'total_rows': 0,
            'total_columns': 0
        }
    }
    
    for sheet_name, df in excel_data.items():
        sheet_content = {
            'name': sheet_name,
            'data': df,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'has_numeric': any(df.select_dtypes(include=['number']).columns),
            'has_text': any(df.select_dtypes(include=['object']).columns)
        }
        
        # Add summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            sheet_content['statistics'] = df[numeric_cols].describe().to_dict()
        
        content['sheets'][sheet_name] = sheet_content
        content['summary']['total_rows'] += len(df)
        content['summary']['total_columns'] += len(df.columns)
    
    return content

def create_powerpoint_presentation(content, pptx_file):
    """Create a comprehensive PowerPoint presentation from the Excel content."""
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
    
    # Summary Slide
    summary_slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(summary_slide_layout)
    title = slide.shapes.title
    title.text = "Summary of Excel Content"
    
    # Add summary table
    rows = len(content['sheets']) + 1
    cols = 4
    left = Inches(1)
    top = Inches(2)
    width = Inches(8)
    height = Inches(0.5 * rows)
    
    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
    
    # Set column widths
    table.columns[0].width = Inches(2)
    table.columns[1].width = Inches(2)
    table.columns[2].width = Inches(2)
    table.columns[3].width = Inches(2)
    
    # Add headers
    headers = ['Sheet Name', 'Rows', 'Columns', 'Content Type']
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = header
        cell.text_frame.paragraphs[0].font.bold = True
    
    # Add data
    for idx, (sheet_name, sheet_data) in enumerate(content['sheets'].items(), 1):
        table.cell(idx, 0).text = sheet_name
        table.cell(idx, 1).text = str(sheet_data['rows'])
        table.cell(idx, 2).text = str(sheet_data['columns'])
        content_types = []
        if sheet_data['has_numeric']:
            content_types.append('Numeric')
        if sheet_data['has_text']:
            content_types.append('Text')
        table.cell(idx, 3).text = ', '.join(content_types)
    
    # Add individual sheet slides
    for sheet_name, sheet_data in content['sheets'].items():
        # Sheet Overview Slide
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = f"Sheet: {sheet_name}"
        
        # Add sheet statistics if available
        if 'statistics' in sheet_data:
            stats_text = "Statistical Summary:\n\n"
            for col, stats in sheet_data['statistics'].items():
                stats_text += f"{col}:\n"
                for stat_name, value in stats.items():
                    stats_text += f"  {stat_name}: {value:.2f}\n"
                stats_text += "\n"
            
            left = Inches(1)
            top = Inches(2)
            width = Inches(8)
            height = Inches(4)
            
            textbox = slide.shapes.add_textbox(left, top, width, height)
            text_frame = textbox.text_frame
            text_frame.text = stats_text
        
        # Data Table Slide
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = f"Data from {sheet_name}"
        
        # Add data table
        df = sheet_data['data']
        rows = len(df) + 1
        cols = len(df.columns)
        
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5)
        
        table = slide.shapes.add_table(rows, cols, left, top, width, height).table
        
        # Add headers
        for col, column_name in enumerate(df.columns):
            cell = table.cell(0, col)
            cell.text = str(column_name)
            cell.text_frame.paragraphs[0].font.bold = True
        
        # Add data
        for row in range(len(df)):
            for col in range(len(df.columns)):
                cell = table.cell(row + 1, col)
                cell.text = str(df.iloc[row, col])
    
    # Save the presentation
    prs.save(pptx_file)

def process_excel_to_pptx(excel_file, pptx_file):
    """Process Excel file and create PowerPoint presentation."""
    # Extract content from Excel
    content = extract_excel_content(excel_file)
    
    # Create PowerPoint presentation
    create_powerpoint_presentation(content, pptx_file)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pptx_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                   os.path.splitext(filename)[0] + '.pptx')
            
            file.save(excel_path)
            process_excel_to_pptx(excel_path, pptx_path)
            
            # Clean up the Excel file
            os.remove(excel_path)
            
            return send_file(pptx_path, as_attachment=True)
        
        return 'Invalid file type. Please upload an Excel file.', 400
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 