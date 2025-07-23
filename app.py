import uuid
from flask import Flask, render_template, request, send_file, jsonify, Response
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os
from werkzeug.utils import secure_filename
import json
import logging
import numpy as np
from datetime import datetime
import shutil
from PIL import Image
import io
import base64
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.dml import MSO_THEME_COLOR
import tempfile
from pptx.dml.color import RGBColor
from docx import Document
import re
import csv
from docx.shared import RGBColor

# --- Template Version 2: Dynamic PPTX Slide Customization ---
try:
    from slide_utils.shape_mapper import build_map
    from slide_utils.format_preserver import inject_text
except ImportError:
    build_map = None
    inject_text = None

TEMPLATE_V2_DIR = 'templates/slide_templates/msa_exec/mainTemp'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CHUNK_SIZE = 15  # Number of rows per slide

def copy_slide_with_full_formatting(source_slide, target_prs):
    """
    Advanced slide copying that preserves ALL formatting, colors, layouts, and media
    """
    try:
        # Create a new slide with blank layout to preserve everything
        blank_layout = target_prs.slide_layouts[6]  # Blank layout
        new_slide = target_prs.slides.add_slide(blank_layout)
        
        # Copy slide background if it exists
        try:
            if source_slide.background.fill.type:
                new_slide.background.fill.solid()
                if hasattr(source_slide.background.fill, 'fore_color'):
                    new_slide.background.fill.fore_color.rgb = source_slide.background.fill.fore_color.rgb
        except Exception as bg_error:
            print(f"Background copying skipped: {bg_error}")
        
        # Copy all shapes with complete formatting preservation
        for shape in source_slide.shapes:
            try:
                copy_shape_with_formatting(shape, new_slide)
            except Exception as shape_error:
                print(f"Error copying shape: {shape_error}")
                continue
        
        return new_slide
        
    except Exception as e:
        print(f"Error in advanced slide copying: {e}")
        # Fallback to basic slide creation
        slide_layout = target_prs.slide_layouts[1]
        slide = target_prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = "Template Slide"
        return slide

def copy_shape_with_formatting(source_shape, target_slide):
    """
    Copy individual shapes with complete formatting preservation
    """
    try:
        shape_type = source_shape.shape_type
        
        if shape_type == MSO_SHAPE_TYPE.TEXT_BOX or shape_type == MSO_SHAPE_TYPE.PLACEHOLDER:
            copy_text_shape_with_formatting(source_shape, target_slide)
        elif shape_type == MSO_SHAPE_TYPE.PICTURE:
            copy_image_shape(source_shape, target_slide)
        elif shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            copy_auto_shape_with_formatting(source_shape, target_slide)
        elif shape_type == MSO_SHAPE_TYPE.GROUP:
            copy_group_shape(source_shape, target_slide)
        elif shape_type == MSO_SHAPE_TYPE.TABLE:
            copy_table_shape(source_shape, target_slide)
        else:
            print(f"Unsupported shape type: {shape_type}")
            
    except Exception as e:
        print(f"Error copying shape type {source_shape.shape_type}: {e}")

def copy_text_shape_with_formatting(source_shape, target_slide):
    """
    Copy text shapes with complete text formatting preservation
    """
    try:
        # Create new text box with exact dimensions and position
        left = source_shape.left
        top = source_shape.top
        width = source_shape.width
        height = source_shape.height
        
        new_textbox = target_slide.shapes.add_textbox(left, top, width, height)
        new_text_frame = new_textbox.text_frame
        
        # Copy text frame properties
        new_text_frame.clear()
        source_text_frame = source_shape.text_frame
        
        # Copy margin settings
        try:
            new_text_frame.margin_bottom = source_text_frame.margin_bottom
            new_text_frame.margin_left = source_text_frame.margin_left
            new_text_frame.margin_right = source_text_frame.margin_right
            new_text_frame.margin_top = source_text_frame.margin_top
        except:
            pass
        
        # Copy word wrap and auto size settings
        try:
            new_text_frame.word_wrap = source_text_frame.word_wrap
            new_text_frame.auto_size = source_text_frame.auto_size
        except:
            pass
        
        # Copy all paragraphs with formatting
        for para_idx, source_para in enumerate(source_text_frame.paragraphs):
            if para_idx == 0:
                new_para = new_text_frame.paragraphs[0]
            else:
                new_para = new_text_frame.add_paragraph()
            
            # Copy paragraph-level formatting
            try:
                new_para.alignment = source_para.alignment
                new_para.level = source_para.level
            except:
                pass
            
            # Copy all runs with character formatting
            for run_idx, source_run in enumerate(source_para.runs):
                if run_idx == 0 and len(new_para.runs) > 0:
                    new_run = new_para.runs[0]
                else:
                    new_run = new_para.add_run()
                
                new_run.text = source_run.text
                
                                 # Copy font properties with enhanced color handling
                try:
                        if source_run.font.name:
                            new_run.font.name = source_run.font.name
                        if source_run.font.size:
                            new_run.font.size = source_run.font.size
                        if source_run.font.bold is not None:
                            new_run.font.bold = source_run.font.bold
                        if source_run.font.italic is not None:
                            new_run.font.italic = source_run.font.italic
                        if source_run.font.underline is not None:
                            new_run.font.underline = source_run.font.underline
                     
                     # Enhanced color copying with multiple fallback methods
                        copy_font_color(source_run.font, new_run.font)
                     
                except Exception as font_error:
                        print(f"Font copying error: {font_error}")
        
        # Copy shape fill and line properties
        copy_shape_appearance(source_shape, new_textbox)
        
    except Exception as e:
        print(f"Error copying text shape: {e}")

def copy_image_shape(source_shape, target_slide):
    """
    Copy image shapes with original formatting
    """
    try:
        # Get image data
        image_stream = io.BytesIO(source_shape.image.blob)
        
        # Add image to target slide
        left = source_shape.left
        top = source_shape.top
        width = source_shape.width
        height = source_shape.height
        
        new_picture = target_slide.shapes.add_picture(image_stream, left, top, width, height)
        
        # Copy shape appearance properties
        copy_shape_appearance(source_shape, new_picture)
        
    except Exception as e:
        print(f"Error copying image: {e}")

def copy_auto_shape_with_formatting(source_shape, target_slide):
    """
    Copy auto shapes (rectangles, circles, etc.) with formatting
    """
    try:
        # Create basic rectangle as placeholder (more complex shapes would need specific handling)
        left = source_shape.left
        top = source_shape.top
        width = source_shape.width
        height = source_shape.height
        
        # Try to preserve the auto shape type
        try:
            new_shape = target_slide.shapes.add_shape(
                source_shape.auto_shape_type, left, top, width, height
            )
        except:
            # Fallback to rectangle
            from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
            new_shape = target_slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, top, width, height
            )
        
        # Copy text if the shape has text
        if hasattr(source_shape, 'text_frame') and source_shape.text_frame:
            copy_text_content(source_shape.text_frame, new_shape.text_frame)
        
        # Copy appearance
        copy_shape_appearance(source_shape, new_shape)
        
    except Exception as e:
        print(f"Error copying auto shape: {e}")

def copy_group_shape(source_shape, target_slide):
    """
    Copy grouped shapes
    """
    try:
        # Note: python-pptx doesn't support creating groups directly
        # We'll copy individual shapes from the group
        for shape in source_shape.shapes:
            copy_shape_with_formatting(shape, target_slide)
    except Exception as e:
        print(f"Error copying group: {e}")

def copy_table_shape(source_shape, target_slide):
    """
    Copy table shapes with formatting
    """
    try:
        source_table = source_shape.table
        rows = len(source_table.rows)
        cols = len(source_table.columns)
        
        left = source_shape.left
        top = source_shape.top
        width = source_shape.width
        height = source_shape.height
        
        new_table_shape = target_slide.shapes.add_table(rows, cols, left, top, width, height)
        new_table = new_table_shape.table
        
        # Copy cell content and formatting
        for row_idx in range(rows):
            for col_idx in range(cols):
                source_cell = source_table.cell(row_idx, col_idx)
                target_cell = new_table.cell(row_idx, col_idx)
                
                # Copy text content
                target_cell.text = source_cell.text
                
                # Copy cell formatting (basic)
                try:
                    if hasattr(source_cell.fill, 'solid'):
                        target_cell.fill.solid()
                        if hasattr(source_cell.fill.fore_color, 'rgb'):
                            target_cell.fill.fore_color.rgb = source_cell.fill.fore_color.rgb
                except:
                    pass
                    
    except Exception as e:
        print(f"Error copying table: {e}")

def copy_shape_appearance(source_shape, target_shape):
    """
    Enhanced visual appearance copying with comprehensive color preservation
    """
    try:
        # Enhanced fill properties copying
        if hasattr(source_shape, 'fill') and hasattr(target_shape, 'fill'):
            try:
                source_fill = source_shape.fill
                target_fill = target_shape.fill
                
                # Copy fill type and properties
                if hasattr(source_fill, 'type') and source_fill.type:
                    from pptx.enum.dml import MSO_FILL_TYPE
                    
                    if source_fill.type == MSO_FILL_TYPE.SOLID:
                        target_fill.solid()
                        # Enhanced color copying for fill
                        copy_shape_color(source_fill.fore_color, target_fill.fore_color)
                    elif source_fill.type == MSO_FILL_TYPE.GRADIENT:
                        # Handle gradient fills if possible
                        print("Gradient fill detected - using solid color fallback")
                        target_fill.solid()
                        if hasattr(source_fill, 'fore_color'):
                            copy_shape_color(source_fill.fore_color, target_fill.fore_color)
                    elif source_fill.type == MSO_FILL_TYPE.PATTERN:
                        # Handle pattern fills
                        print("Pattern fill detected - using solid color fallback")
                        target_fill.solid()
                        if hasattr(source_fill, 'fore_color'):
                            copy_shape_color(source_fill.fore_color, target_fill.fore_color)
                            
            except Exception as fill_error:
                print(f"Fill copying error: {fill_error}")
        
        # Enhanced line properties copying
        if hasattr(source_shape, 'line') and hasattr(target_shape, 'line'):
            try:
                source_line = source_shape.line
                target_line = target_shape.line
                
                # Copy line width
                if hasattr(source_line, 'width') and source_line.width:
                    target_line.width = source_line.width
                
                # Copy line color with enhanced method
                if hasattr(source_line, 'color') and hasattr(target_line, 'color'):
                    copy_shape_color(source_line.color, target_line.color)
                
                # Copy line style if available
                if hasattr(source_line, 'dash_style') and hasattr(target_line, 'dash_style'):
                    try:
                        target_line.dash_style = source_line.dash_style
                    except:
                        pass
                        
            except Exception as line_error:
                print(f"Line copying error: {line_error}")
        
        # Copy shadow properties if available
        if hasattr(source_shape, 'shadow') and hasattr(target_shape, 'shadow'):
            try:
                source_shadow = source_shape.shadow
                target_shadow = target_shape.shadow
                
                # Basic shadow copying
                if hasattr(source_shadow, 'inherit') and not source_shadow.inherit:
                    target_shadow.inherit = False
                    
            except Exception as shadow_error:
                print(f"Shadow copying error: {shadow_error}")
                
    except Exception as e:
        print(f"Error copying appearance: {e}")

def copy_shape_color(source_color, target_color):
    """
    Enhanced color copying for shape fills and lines
    """
    try:
        # Method 1: RGB color copying
        if hasattr(source_color, 'rgb') and source_color.rgb is not None:
            target_color.rgb = source_color.rgb
            print(f"Copied shape RGB color: {source_color.rgb}")
            return
            
        # Method 2: Theme color copying
        if hasattr(source_color, 'theme_color') and source_color.theme_color is not None:
            target_color.theme_color = source_color.theme_color
            print(f"Copied shape theme color: {source_color.theme_color}")
            
            # Also copy brightness/tint if available
            if hasattr(source_color, 'brightness') and source_color.brightness is not None:
                if hasattr(target_color, 'brightness'):
                    target_color.brightness = source_color.brightness
                    
        # Method 3: Try color type specific copying
        if hasattr(source_color, 'type'):
            from pptx.enum.dml import MSO_COLOR_TYPE
            try:
                color_type = source_color.type
                if color_type == MSO_COLOR_TYPE.RGB and source_color.rgb:
                    target_color.rgb = source_color.rgb
                elif color_type == MSO_COLOR_TYPE.THEME and hasattr(source_color, 'theme_color'):
                    target_color.theme_color = source_color.theme_color
            except Exception as type_error:
                print(f"Color type copying error: {type_error}")
                
    except Exception as color_error:
        print(f"Shape color copying error: {color_error}")

def copy_font_color(source_font, target_font):
    """
    Enhanced font color copying with multiple methods for maximum compatibility
    """
    try:
        # Method 1: Try RGB color copying
        if hasattr(source_font.color, 'rgb') and source_font.color.rgb is not None:
            target_font.color.rgb = source_font.color.rgb
            print(f"Copied RGB color: {source_font.color.rgb}")
            return
        
        # Method 2: Try theme color copying
        if hasattr(source_font.color, 'theme_color') and source_font.color.theme_color is not None:
            target_font.color.theme_color = source_font.color.theme_color
            print(f"Copied theme color: {source_font.color.theme_color}")
            return
            
        # Method 3: Try brightness adjustment if available
        if hasattr(source_font.color, 'brightness') and source_font.color.brightness is not None:
            if hasattr(target_font.color, 'brightness'):
                target_font.color.brightness = source_font.color.brightness
                print(f"Copied brightness: {source_font.color.brightness}")
        
        # Method 4: Try color type and set accordingly
        if hasattr(source_font.color, 'type'):
            color_type = source_font.color.type
            print(f"Source color type: {color_type}")
            
            # Handle different color types
            from pptx.enum.dml import MSO_COLOR_TYPE
            try:
                if color_type == MSO_COLOR_TYPE.RGB:
                    if source_font.color.rgb:
                        target_font.color.rgb = source_font.color.rgb
                elif color_type == MSO_COLOR_TYPE.THEME:
                    if hasattr(source_font.color, 'theme_color'):
                        target_font.color.theme_color = source_font.color.theme_color
                elif color_type == MSO_COLOR_TYPE.SCHEME:
                    # Handle scheme colors if possible
                    print("Scheme color detected - using fallback")
            except Exception as color_type_error:
                print(f"Color type handling error: {color_type_error}")
        
    except Exception as color_error:
        print(f"Font color copying error: {color_error}")
        # Fallback: try to extract any available color information
        try:
            # Last resort: try to copy any color attributes that exist
            if hasattr(source_font.color, '_color_val') and hasattr(target_font.color, '_color_val'):
                target_font.color._color_val = source_font.color._color_val
                print("Used fallback color copying method")
        except:
            print("All color copying methods failed - using default color")

def copy_text_content(source_text_frame, target_text_frame):
    """
    Helper function to copy text content between text frames
    """
    try:
        target_text_frame.clear()
        
        for para_idx, source_para in enumerate(source_text_frame.paragraphs):
            if para_idx == 0:
                target_para = target_text_frame.paragraphs[0]
            else:
                target_para = target_text_frame.add_paragraph()
            
            target_para.text = source_para.text
            try:
                target_para.alignment = source_para.alignment
            except:
                pass
                
    except Exception as e:
        print(f"Error copying text content: {e}")

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

def normalize_placeholder_key(key):
    """Return only the key as-is for direct matching (no variants)."""
    return [key.strip()]

def strip_brackets(placeholder):
    """Remove surrounding brackets from a placeholder if present."""
    s = placeholder.strip()
    if s.startswith('[') and s.endswith(']'):
        return s[1:-1].strip()
    return s

def replace_placeholders_in_docx(doc: Document, mapping: dict):
    """
    Replace all placeholders in the DOCX document with their corresponding values from mapping.
    Handles split runs and preserves formatting.
    Only replaces exact keys as provided in the mapping, and only if the value is non-empty.
    Ensures font and bold/italic consistency after replacement.
    Excludes brackets from the replaced value.
    """
    def replace_in_runs(runs, mapping):
        # Gather original formatting from the first run
        if runs:
            first_run = runs[0]
            orig_font_name = first_run.font.name
            orig_font_size = first_run.font.size
            orig_bold = first_run.font.bold
            orig_italic = first_run.font.italic
        else:
            orig_font_name = orig_font_size = orig_bold = orig_italic = None
        full_text = ''.join(run.text for run in runs)
        for key, value in mapping.items():
            if not value.strip():
                continue  # Skip empty values
            for variant in normalize_placeholder_key(key):
                # Replace the placeholder, but exclude brackets in the output
                full_text = full_text.replace(variant, value)
                # Also replace the bracketless version if present
                bracketless = strip_brackets(variant)
                if bracketless != variant:
                    full_text = full_text.replace(bracketless, value)
        # Re-split the new text into the same number of runs
        idx = 0
        for run in runs:
            run_len = len(run.text)
            run.text = full_text[idx:idx+run_len]
            # Apply consistent formatting
            run.font.name = orig_font_name
            run.font.size = orig_font_size
            run.font.bold = orig_bold
            run.font.italic = orig_italic
            idx += run_len

    def process_paragraph(paragraph, mapping):
        if not paragraph.runs:
            return
        joined = ''.join(run.text for run in paragraph.runs)
        if any(variant in joined for key, value in mapping.items() if value.strip() for variant in normalize_placeholder_key(key)):
            replace_in_runs(paragraph.runs, mapping)

    def process_table(table, mapping):
        for row in table.rows:
            for cell in row.cells:
                process_block(cell, mapping)

    def process_block(block, mapping):
        for paragraph in block.paragraphs:
            process_paragraph(paragraph, mapping)
        for table in getattr(block, 'tables', []):
            process_table(table, mapping)

    # Main document
    for paragraph in doc.paragraphs:
        process_paragraph(paragraph, mapping)
    for table in doc.tables:
        process_table(table, mapping)
    # Headers and footers
    for section in doc.sections:
        header = section.header
        footer = section.footer
        process_block(header, mapping)
        process_block(footer, mapping)
    return doc

def replace_placeholders_in_docx_with_track_changes(doc: Document, mapping: dict):
    """
    Instead of direct replacement, highlight the placeholder and replace it with the new value (no brackets) as a suggestion.
    Only replaces exact keys as provided in the mapping, and only if the value is non-empty.
    Excludes brackets from the replaced value.
    """
    def process_paragraph(paragraph, mapping):
        for run in paragraph.runs:
            for key, value in mapping.items():
                if not value.strip():
                    continue  # Skip empty values
                replaced = False
                for variant in normalize_placeholder_key(key):
                    # Replace the placeholder, but exclude brackets in the output
                    if variant in run.text:
                        run.text = run.text.replace(variant, value)
                        run.font.highlight_color = 7  # yellow
                        replaced = True
                        break
                    # Also replace the bracketless version if present
                    bracketless = strip_brackets(variant)
                    if bracketless != variant and bracketless in run.text:
                        run.text = run.text.replace(bracketless, value)
                        run.font.highlight_color = 7  # yellow
                        replaced = True
                        break
                if replaced:
                    break

    def process_table(table, mapping):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    process_paragraph(paragraph, mapping)

    # Main document
    for paragraph in doc.paragraphs:
        process_paragraph(paragraph, mapping)
    for table in doc.tables:
        process_table(table, mapping)
    # Headers and footers
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            process_paragraph(paragraph, mapping)
        for paragraph in section.footer.paragraphs:
            process_paragraph(paragraph, mapping)
    return doc

def parse_kv_table_file(file_storage):
    """
    Parse a 2-column CSV or Excel file into a list of {'key': ..., 'value': ...} dicts.
    The first row is treated as the document name (not a key-value pair).
    """
    filename = file_storage.filename.lower()
    mapping = []
    document_name = None
    if filename.endswith('.csv'):
        file_storage.stream.seek(0)
        reader = csv.reader((line.decode('utf-8') for line in file_storage.stream), delimiter=',')
        rows = list(reader)
        if rows:
            document_name = rows[0][0].strip() if rows[0] and rows[0][0] else 'lease_population_filled'
            for row in rows[1:]:
                if len(row) >= 2:
                    mapping.append({'key': row[0].strip(), 'value': row[1].strip()})
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = pd.read_excel(file_storage, header=None)
        if not df.empty:
            document_name = str(df.iloc[0,0]).strip() if not pd.isnull(df.iloc[0,0]) else 'lease_population_filled'
            for _, row in df.iloc[1:].iterrows():
                if len(row) >= 2:
                    mapping.append({'key': str(row[0]).strip(), 'value': str(row[1]).strip()})
    else:
        raise ValueError('Unsupported file type')
    # Remove header row if it looks like a header (after document name row)
    if mapping and mapping[0]['key'].lower() in ('key', 'placeholder') and mapping[0]['value'].lower() in ('value', 'replacement'):
        mapping = mapping[1:]
    return mapping, document_name

@app.route('/parse_kv_table', methods=['POST'])
def parse_kv_table():
    """
    Accept a 2-column CSV or Excel file and return a key-value mapping as JSON.
    The first row is treated as the document name.
    """
    if 'table_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['table_file']
    try:
        mapping, document_name = parse_kv_table_file(file)
        # Validate
        keys = [pair['key'] for pair in mapping]
        if any(not k for k in keys) or len(set(keys)) != len(keys):
            return jsonify({'error': 'Keys must be non-empty and unique'}), 400
        return jsonify({'mapping': mapping, 'document_name': document_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# --- Track Changes Replacement Logic ---
def add_comment_to_run(run, comment_text):
    """
    Add a comment to a run. python-docx does not support comments natively as of 2024.
    This is a limitation. As a workaround, we can highlight the run and append the new value in brackets.
    """
    # Highlight the run (yellow)
    run.font.highlight_color = 7  # 7 = yellow in MS Word
    # Append the suggestion as [NEW: value]
    run.text += f" [NEW: {comment_text}]"
    # Note: True Word comments/revisions are not supported by python-docx as of 2024.
    # If/when support is added, this is where to insert a real comment.


def remove_acknowledgment_block(doc, keep_type):
    """
    Remove the acknowledgment block for the non-selected party type.
    - keep_type: 'Entity or Trust' or 'Individual'
    - The block to remove starts at its header and includes all following paragraphs up to the next block's header or end of document.
    - If both or neither block is found, insert a placeholder or error message.
    """
    # Define headers (case-insensitive, strip whitespace)
    header_entity = 'acknowledgment block for entity or trust'
    header_individual = 'acknowledgment block for individual'
    # Determine which to keep/remove
    if keep_type.lower() == 'entity or trust':
        header_remove = header_individual
        header_keep = header_entity
    else:
        header_remove = header_entity
        header_keep = header_individual
    # Find all paragraphs
    paragraphs = doc.paragraphs
    idx_remove = None
    idx_keep = None
    for i, p in enumerate(paragraphs):
        text = p.text.strip().lower()
        if text == header_remove:
            idx_remove = i
        if text == header_keep:
            idx_keep = i
    # If both or neither found, insert error/placeholder
    if idx_remove is None or idx_keep is None or idx_remove == idx_keep:
        doc.add_paragraph('[ERROR: Could not find both acknowledgment blocks for removal. Please check your template.]')
        return doc
    # Determine block to remove: from idx_remove up to (but not including) idx_keep or end
    start = idx_remove
    end = idx_keep if idx_keep > idx_remove else len(paragraphs)
    for i in range(end-1, start-1, -1):
        p = paragraphs[i]._element
        p.getparent().remove(p)
    return doc

def remove_entity_signature_block(doc):
    """
    Remove the '[Trust/Entity Name]' signature block and its following lines (By:, Name:, Title:) if present.
    """
    sig_header = '[trust/entity name]'
    sig_lines = ['by:', 'name:', 'title:']
    paragraphs = doc.paragraphs
    idx_sig = None
    for i, p in enumerate(paragraphs):
        if p.text.strip().lower() == sig_header:
            idx_sig = i
            break
    if idx_sig is not None:
        end = min(idx_sig + 4, len(paragraphs))
        for i in range(end-1, idx_sig-1, -1):
            p = paragraphs[i]._element
            p.getparent().remove(p)
    return doc

def remove_acknowledgment_blocks_enforced(doc, grantee_type):
    """
    Remove or retain sections based on grantee_type ('Individual' or 'Entity or Trust') using explicit start/end markers.
    For individuals:
      - Remove entity sections:
        1. [Trust/Entity Name] → My Commission Expires:___
        2. Acknowledgment Block for Entity or Trust → (Signature of Notary Public)
    For entities:
      - Remove individual sections:
        1. GRANTOR: → Name:
        2. Acknowledgment Block for Individual → (Signature of Notary Public)
    Only the relevant sections remain in the final document.
    If a marker is not found, return a clear error message.
    """
    grantee_type = grantee_type.strip().lower()
    paragraphs = doc.paragraphs
    def find_section_indices(start_marker, end_marker, section_label):
        indices = []
        start = None
        start_idx = None
        for i, p in enumerate(paragraphs):
            text = p.text.strip().lower()
            if start is None and start_marker.strip().lower() in text:
                start = i
                start_idx = i
            elif start is not None and end_marker.strip().lower() in text:
                indices.append((start, i))
                start = None
        if start is not None:
            context = '\n'.join(f'{j}: {paragraphs[j].text}' for j in range(max(0, start_idx-2), min(len(paragraphs), start_idx+5)))
            raise Exception(f"Could not find END marker '{end_marker}' for section '{section_label}'.\nContext:\n{context}")
        if not indices and start_marker:
            context = '\n'.join(f'{j}: {paragraphs[j].text}' for j in range(len(paragraphs)))
            raise Exception(f"Could not find START marker '{start_marker}' for section '{section_label}'.\nParagraphs:\n{context}")
        return indices
    to_remove = []
    if grantee_type == 'individual':
        # Remove entity sections
        entity1 = find_section_indices('[trust/entity name]', 'my commission expires:___', 'Entity Section 1')
        entity2 = find_section_indices('acknowledgment block for entity or trust', '(signature of notary public)', 'Entity Section 2')
        to_remove.extend(entity1)
        to_remove.extend(entity2)
    else:
        # Remove individual sections
        ind1 = find_section_indices('grantor:', 'name:', 'Individual Section 1')
        ind2 = find_section_indices('acknowledgment block for individual', '(signature of notary public)', 'Individual Section 2')
        to_remove.extend(ind1)
        to_remove.extend(ind2)
    for start, end in sorted(to_remove, reverse=True):
        for i in range(end, start-1, -1):
            p = paragraphs[i]._element
            p.getparent().remove(p)
    return doc

# Update lease_population_replace to use the new enforcement function
@app.route('/lease_population_replace', methods=['POST'])
def lease_population_replace():
    """
    Endpoint to process DOCX file and replace placeholders with user-provided values.
    Streams the modified DOCX back to the user.
    Accepts 'track_changes' flag ("true" or "false"), 'document_name', and 'party_type'.
    If a replacement value is blank, the original placeholder is left in place.
    """
    if 'docx' not in request.files or 'mapping' not in request.form:
        return jsonify({'error': 'Missing file or mapping'}), 400
    docx_file = request.files['docx']
    mapping_json = request.form['mapping']
    track_changes = request.form.get('track_changes', 'false').lower() == 'true'
    document_name = request.form.get('document_name', 'lease_population_filled')
    party_type = request.form.get('party_type', None)
    try:
        # Only include keys with non-empty values in the mapping
        mapping_raw = json.loads(mapping_json)
        mapping = {item['key']: item['value'] for item in mapping_raw if item['value'].strip()}
    except Exception as e:
        return jsonify({'error': 'Invalid mapping format'}), 400
    # Validate keys
    if not mapping_raw or any(not item['key'] for item in mapping_raw) or len(set(item['key'] for item in mapping_raw)) != len(mapping_raw):
        return jsonify({'error': 'Invalid or duplicate keys'}), 400
    if not party_type:
        return jsonify({'error': 'Party type is required'}), 400
    # Process DOCX
    try:
        doc = Document(docx_file)
        if track_changes:
            doc = replace_placeholders_in_docx_with_track_changes(doc, mapping)
        else:
            doc = replace_placeholders_in_docx(doc, mapping)
        # Enforce only one acknowledgment block remains
        doc = remove_acknowledgment_blocks_enforced(doc, party_type)
        # Remove entity signature block if party_type is Individual
        if party_type == 'Individual':
            doc = remove_entity_signature_block(doc)
        # Stream back as download
        from io import BytesIO
        out_stream = BytesIO()
        doc.save(out_stream)
        out_stream.seek(0)
        safe_name = document_name.replace(' ', '_').replace('/', '_')
        return send_file(out_stream, as_attachment=True, download_name=f'{safe_name}.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        return jsonify({'error': f'Failed to process DOCX: {str(e)}'}), 500

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

@app.route('/get_slide_preview/<slide_id>')
def get_slide_preview(slide_id):
    """Get a preview of a specific slide"""
    try:
        # Map slide IDs to their actual .pptx files
        slide_file_mapping = {
            'title-1': 'templates/slide_templates/msa_exec/Title/msa[title].pptx',
            # Add more mappings as you add more slides
        }
        
        if slide_id not in slide_file_mapping:
            return jsonify({'error': 'Slide not found'}), 404
        
        pptx_path = slide_file_mapping[slide_id]
        if not os.path.exists(pptx_path):
            return jsonify({'error': 'Slide file not found'}), 404
        
        # Load the presentation and get the first slide
        prs = Presentation(pptx_path)
        if len(prs.slides) == 0:
            return jsonify({'error': 'No slides in presentation'}), 404
        
        slide = prs.slides[0]  # Get the first slide
        
        # Extract slide content and formatting for preview
        slide_content = {
            'title': '',
            'content': [],
            'layout': slide.slide_layout.name if hasattr(slide.slide_layout, 'name') else 'Unknown',
            'background': {},
            'shapes': []
        }

        # Extract background color (solid only for now)
        try:
            bg = slide.background
            if hasattr(bg, 'fill') and bg.fill.type == 1:  # MSO_FILL_TYPE.SOLID
                if hasattr(bg.fill, 'fore_color') and hasattr(bg.fill.fore_color, 'rgb') and bg.fill.fore_color.rgb:
                    slide_content['background']['type'] = 'solid'
                    slide_content['background']['color'] = str(bg.fill.fore_color.rgb)
        except Exception as bg_error:
            print(f"Background extraction skipped: {bg_error}")

        # Extract all shapes with formatting
        if hasattr(slide, 'shapes'):
            for shape in slide.shapes:
                try:
                    shape_info = {
                        'type': str(shape.shape_type),
                        'left': int(shape.left),
                        'top': int(shape.top),
                        'width': int(shape.width),
                        'height': int(shape.height),
                        'is_title': False,
                        'text': '',
                        'font': {},
                        'alignment': None
                    }
                    if hasattr(shape, 'text') and shape.text.strip():
                        # Check if it's a title placeholder
                        is_title = False
                        try:
                            if hasattr(shape, 'placeholder_format'):
                                is_title = shape.placeholder_format.type == 1  # Title placeholder
                        except:
                            if shape.top < Inches(2) and shape.width > Inches(6):
                                is_title = True
                        shape_info['is_title'] = is_title
                        shape_info['text'] = shape.text
                        # Extract font and alignment from first paragraph/run
                        if hasattr(shape, 'text_frame') and shape.text_frame.paragraphs:
                            para = shape.text_frame.paragraphs[0]
                            if para.runs and len(para.runs) > 0:
                                run = para.runs[0]
                                font = run.font
                                shape_info['font'] = {
                                    'name': font.name,
                                    'size': int(font.size.pt) if font.size else None,
                                    'bold': font.bold,
                                    'italic': font.italic,
                                    'color': str(font.color.rgb) if font.color and font.color.rgb else None
                                }
                            shape_info['alignment'] = str(para.alignment) if para.alignment else None
                        if is_title:
                            slide_content['title'] = shape.text
                        else:
                            slide_content['content'].append(shape.text)
                    slide_content['shapes'].append(shape_info)
                except Exception as shape_error:
                    print(f"Skipping shape due to error: {shape_error}")
                    continue

        return jsonify({
            'success': True,
            'slide_id': slide_id,
            'preview': slide_content
        })
        
    except Exception as e:
        print(f"Error getting slide preview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated presentation files"""
    try:
        file_path = os.path.join('uploads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_msa_template', methods=['POST'])
def generate_msa_template():
    try:
        data = request.get_json()
        selected_slides = data.get('selected_slides', [])
        dynamic_variables = data.get('dynamic_variables', {})
        
        if not selected_slides:
            return jsonify({'error': 'No slides selected'}), 400
        
        # Create PowerPoint presentation
        prs = Presentation()
        
        # Map slide IDs to their actual .pptx files
        slide_file_mapping = {
            'title-1': ('templates/slide_templates/msa_exec/Title/msa[title].pptx', 0),
            'exec-summary-1': ('templates/slide_templates/msa_exec/Executive_Summary/ExecSummary.pptx', 0),
            'module-procurement-strategy': ('templates/slide_templates/msa_exec/Module_procurement/mp.pptx', 0),
            'module-procurement-supplier': ('templates/slide_templates/msa_exec/Module_procurement/mp.pptx', 1),
            'module-procurement-timeline': ('templates/slide_templates/msa_exec/Module_procurement/mp.pptx', 2),
            'module-procurement-cost': ('templates/slide_templates/msa_exec/Module_procurement/mp.pptx', 3),
            # Add more mappings as you add more slides to other sections
        }
        
        print(f"Generating template with {len(selected_slides)} slides")
        
        # Process slides in the order they were selected
        for idx, slide_info in enumerate(selected_slides):
            slide_id = slide_info['id']
            edited_shapes = slide_info.get('edited_shapes', None)
            page_number = idx + 1
            
            if slide_id in slide_file_mapping:
                # Use actual .pptx file
                pptx_path, slide_idx = slide_file_mapping[slide_id]
                if os.path.exists(pptx_path):
                    print(f"Adding slide from: {pptx_path}")
                    # Load the template slide
                    template_prs = Presentation(pptx_path)
                    if len(template_prs.slides) > 0:
                        template_slide = template_prs.slides[slide_idx]
                        # Use advanced slide copying to preserve ALL formatting
                        print(f"Copying slide with full formatting preservation...")
                        slide = copy_slide_with_full_formatting(template_slide, prs)
                        # --- DYNAMIC CONTENT INSERTION ---
                        if edited_shapes:
                            shape_idx = 0
                            for shape in list(slide.shapes):
                                if not hasattr(shape, 'text_frame'):
                                    continue
                                # First text box (text one)
                                if shape_idx == 0:
                                    shape.text = edited_shapes[0] if len(edited_shapes) > 0 and edited_shapes[0] else 'August 2024'
                                    shape.left = Inches(0.7)
                                    shape.top = Inches(2.5)
                                    shape.width = shape.width  # keep original width
                                    shape.height = shape.height  # keep original height
                                    # Style: white, bold
                                    for para in shape.text_frame.paragraphs:
                                        para.font.bold = True
                                        para.font.color.rgb = RGBColor(255, 255, 255)
                                # Second text box (page number)
                                elif shape_idx == 1:
                                    # Use edited value, else '1' as placeholder
                                    shape.text = edited_shapes[1] if len(edited_shapes) > 1 and edited_shapes[1] else '1'
                                    for para in shape.text_frame.paragraphs:
                                        para.font.bold = True
                                        para.font.size = Pt(18)
                                        para.font.color.rgb = RGBColor(255, 255, 255)
                                        para.alignment = PP_ALIGN.RIGHT
                                    shape.left = Inches(12)
                                    shape.top = Inches(7)
                                    shape.width = Inches(0.7)
                                    shape.height = Inches(0.3)
                                # Remove any third or later text boxes
                                elif shape_idx >= 2:
                                    slide.shapes._spTree.remove(shape._element)
                                shape_idx += 1
                                # Remove outline from all text boxes
                                if hasattr(shape, 'line') and hasattr(shape.line, 'fill'):
                                    shape.line.fill.background()
                        # Remove any extra text boxes if more than 2 remain
                        text_shapes = [s for s in slide.shapes if hasattr(s, 'text_frame')]
                        while len(text_shapes) > 2:
                            slide.shapes._spTree.remove(text_shapes[-1]._element)
                            text_shapes = [s for s in slide.shapes if hasattr(s, 'text_frame')]
                        # Remove outline from all text boxes (again, for added boxes)
                        for shape in text_shapes:
                            if hasattr(shape, 'line') and hasattr(shape.line, 'fill'):
                                shape.line.fill.background()
                        # Ensure both text boxes exist, add if missing
                        if len(text_shapes) < 2:
                            if len(text_shapes) == 0:
                                # Add text one
                                text_one = slide.shapes.add_textbox(Inches(0.7), Inches(2.5), Inches(4), Inches(1))
                                text_one.text_frame.text = edited_shapes[0] if edited_shapes and len(edited_shapes) > 0 else 'August 2024'
                                for para in text_one.text_frame.paragraphs:
                                    para.font.bold = True
                                    para.font.color.rgb = RGBColor(255, 255, 255)
                            # Add page number
                            page_num_box = slide.shapes.add_textbox(Inches(12), Inches(7), Inches(0.7), Inches(0.3))
                            page_num_frame = page_num_box.text_frame
                            page_num_frame.text = edited_shapes[1] if edited_shapes and len(edited_shapes) > 1 and edited_shapes[1] else '1'
                            for para in page_num_frame.paragraphs:
                                para.font.size = Pt(18)
                                para.font.bold = True
                                para.font.color.rgb = RGBColor(255, 255, 255)
                                para.alignment = PP_ALIGN.RIGHT
            else:
                # Fallback to text-based content for slides without .pptx templates
                print(f"Using text template for slide: {slide_id}")
                slide_layout = prs.slide_layouts[1]  # Title and Content layout
                slide = prs.slides.add_slide(slide_layout)
                # Set title
                title = slide.shapes.title
                if edited_shapes and 'title' in edited_shapes:
                    title.text = edited_shapes['title']
                else:
                    title.text = slide_info.get('label', f'Slide {slide_id}')
                # Style title: white, bold
                for para in title.text_frame.paragraphs:
                    para.font.bold = True
                    para.font.size = Pt(32)
                    para.font.color.rgb = RGBColor(255, 255, 255)
                # Add placeholder content
                if len(slide.placeholders) > 1:
                    content = slide.placeholders[1]
                    if edited_shapes and 'content' in edited_shapes and len(edited_shapes['content']) > 0:
                        content.text = '\n'.join(edited_shapes['content'])
                    else:
                        content.text = f"Content for {slide_info.get('label', slide_id)}\n\nThis slide template will be enhanced with actual content."
                # --- PAGE NUMBER ---
                left = Inches(8.5)
                top = Inches(6.7)
                width = Inches(1.3)
                height = Inches(0.5)
                page_num_box = slide.shapes.add_textbox(left, top, width, height)
                page_num_frame = page_num_box.text_frame
                page_num_frame.text = str(page_number)
                for para in page_num_frame.paragraphs:
                    para.font.size = Pt(18)
                    para.font.bold = True
                    para.font.color.rgb = RGBColor(255, 255, 255)
                    para.alignment = PP_ALIGN.RIGHT
        
        # Save presentation with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"MSA_Execution_Template_{timestamp}.pptx"
        output_path = os.path.join('uploads', output_filename)
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        
        prs.save(output_path)
        
        print(f"Template saved successfully: {output_filename}")
        
        return jsonify({
            'success': True,
            'message': f'Custom template generated successfully with {len(selected_slides)} slides',
            'filename': output_filename,
            'download_url': f'/download/{output_filename}',
            'slides_included': [slide['label'] for slide in selected_slides]
        })
        
    except Exception as e:
        print(f"Error generating MSA template: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def retrieve_slide_content(slide_config, variables):
    """
    Retrieve slide content from templates and integrate dynamic variables
    """
    section = slide_config['section']
    slide_id = slide_config.get('template_file', '').replace('.json', '')
    
    # Template content mapping with dynamic variable integration
    content_templates = {
        # Title Section
        'title_slide': f"""MSA Execution Overview - {variables['project_name']}

• Master Service Agreement Implementation
• Project Capacity: {variables['capacity']}
• Total Investment: {variables['project_cost']}
• Key Stakeholders and Responsibilities
• Risk Management Framework
• Expected Completion: {variables['date']}""",

        # Executive Summary
        'executive_summary': f"""Executive Summary - {variables['project_name']}

• Project Objectives: Deploy {variables['capacity']} renewable energy system
• Total Investment: {variables['project_cost']}
• Expected IRR: {variables['irr']}
• Contract Term: {variables['contract_term']}
• Key Deliverables and Milestones
• Success Metrics and KPIs""",

        # Module Procurement
        'procurement_strategy': f"""Procurement Strategy - {variables['project_name']}

• Strategic Sourcing Approach for {variables['capacity']} system
• Supplier Market Analysis
• Procurement Methodology and Standards
• Quality Assurance Framework
• Cost Optimization Target: 5-10% savings
• Timeline: Q1-Q3 {variables['date']}""",

        'supplier_selection': f"""Supplier Selection Criteria

• Technical Capabilities: {variables['capacity']} scale experience
• Financial Stability: Minimum $50M revenue
• Past Performance: 95%+ delivery success rate
• Quality Certifications: ISO 9001, IEC standards
• Risk Assessment: Financial and operational risks
• Geographic Presence: Local support capabilities""",

        'procurement_timeline': f"""Procurement Timeline - {variables['project_name']}

• RFP Release: January {variables['date'].split()[-1]}
• Proposal Submission: March {variables['date'].split()[-1]}
• Technical Evaluation: April {variables['date'].split()[-1]}
• Commercial Negotiation: May {variables['date'].split()[-1]}
• Contract Award: June {variables['date'].split()[-1]}
• Delivery Schedule: Q3-Q4 {variables['date'].split()[-1]}""",

        'cost_analysis': f"""Cost Analysis and Budget

• Total Budget: {variables['project_cost']}
• Unit Costs: {float(variables['project_cost'].replace('$', '').replace(',', '')) / float(variables['capacity'].replace(' MW', '')):.0f}k per MW
• Equipment Costs: 65% of total budget
• Installation & Commissioning: 25%
• Soft Costs & Contingency: 10%
• Payment Terms: Progressive payments""",

        'risk_assessment': f"""Risk Assessment and Mitigation

• Supply Chain Risks: Material availability, logistics
• Quality Risks: Performance degradation, warranty
• Schedule Risks: Weather, permitting delays
• Cost Risks: Material price volatility
• Mitigation: Multiple suppliers, insurance, contracts
• Contingency Fund: 10% of {variables['project_cost']}""",

        # Gen-Tie EPC
        'epc_overview': f"""EPC Agreement Overview - {variables['project_name']}

• Scope: Complete {variables['capacity']} system delivery
• Contract Value: {variables['project_cost']}
• Performance Standards: 98%+ availability
• Delivery Timeline: 18 months
• Quality Standards: IEC/IEEE compliance
• Warranty: 25-year performance guarantee""",

        'technical_specs': f"""Technical Specifications

• System Capacity: {variables['capacity']}
• Annual Production: {variables['annual_production']}
• Performance Ratio: >85%
• System Efficiency: >20%
• Grid Compliance: IEEE 1547 standards
• Environmental Rating: IEC 61215/61730""",

        'delivery_schedule': f"""Delivery Schedule and Milestones

• Project Kickoff: Q1 {variables['date'].split()[-1]}
• Design & Engineering: Q1-Q2 {variables['date'].split()[-1]}
• Procurement & Manufacturing: Q2-Q3 {variables['date'].split()[-1]}
• Installation & Construction: Q3-Q4 {variables['date'].split()[-1]}
• Testing & Commissioning: Q4 {variables['date'].split()[-1]}
• Commercial Operation: Q1 {int(variables['date'].split()[-1]) + 1}""",

        'performance_guarantees': f"""Performance Guarantees

• System Availability: >98% annually
• Performance Ratio: >85% in year 1
• Power Output: {variables['capacity']} ± 3%
• Annual Production: {variables['annual_production']} ± 5%
• Degradation Rate: <0.5% per year
• Warranty Period: {variables['contract_term']}""",

        # PPA Updates
        'ppa_status': f"""PPA Status and Updates

• Contract Capacity: {variables['capacity']}
• Contract Price: {variables['energy_price']}
• Term: {variables['contract_term']}
• Annual Escalation: {variables['escalation_rate']}
• Current Status: Under negotiation
• Expected Execution: Q2 {variables['date'].split()[-1]}""",

        'commercial_terms': f"""Commercial Terms and Conditions

• Contract Price: {variables['energy_price']}
• Contract Term: {variables['contract_term']}
• Annual Escalation: {variables['escalation_rate']}
• Performance Requirements: >95% availability
• Settlement: Monthly energy delivery
• Credit Requirements: Investment grade""",

        'ppa_timeline': f"""PPA Timeline and Next Steps

• Term Sheet: Completed
• Contract Negotiation: In progress
• Regulatory Approval: Q2 {variables['date'].split()[-1]}
• Financial Close: Q3 {variables['date'].split()[-1]}
• Commercial Operation: Q1 {int(variables['date'].split()[-1]) + 1}
• First Energy Delivery: Q1 {int(variables['date'].split()[-1]) + 1}""",

        # Economics and Finance
        'financial_overview': f"""Financial Overview and Assumptions

• Total Project Cost: {variables['project_cost']}
• Revenue Projections: {float(variables['annual_production'].replace(',', '').replace(' MWh', '')) * float(variables['energy_price'].replace('$', '').replace('/MWh', '')) / 1000000:.1f}M annually
• Project IRR: {variables['irr']}
• Debt/Equity Ratio: {variables['debt_equity_ratio']}
• Capacity Factor: 28%
• Contract Escalation: {variables['escalation_rate']}""",

        'capex_analysis': f"""Capital Expenditure Analysis

• Total CapEx: {variables['project_cost']}
• Equipment Costs: 65% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.65 / 1000000:.1f}M)
• Installation Costs: 25% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.25 / 1000000:.1f}M)
• Soft Costs: 7% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.07 / 1000000:.1f}M)
• Contingency: 3% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.03 / 1000000:.1f}M)
• Cost per MW: {float(variables['project_cost'].replace('$', '').replace(',', '')) / float(variables['capacity'].replace(' MW', '')) / 1000:.1f}M/MW""",

        'revenue_projections': f"""Revenue Projections

• Annual Energy Production: {variables['annual_production']}
• Contract Price (Year 1): {variables['energy_price']}
• Annual Revenue (Year 1): ${float(variables['annual_production'].replace(',', '').replace(' MWh', '')) * float(variables['energy_price'].replace('$', '').replace('/MWh', '')) / 1000000:.1f}M
• Annual Escalation: {variables['escalation_rate']}
• 25-Year Revenue (Nominal): ${float(variables['annual_production'].replace(',', '').replace(' MWh', '')) * float(variables['energy_price'].replace('$', '').replace('/MWh', '')) * 25 * 1.15 / 1000000:.0f}M
• Capacity Factor: 28%""",

        'cash_flow': f"""Cash Flow Analysis

• Project IRR: {variables['irr']}
• NPV (10% discount): {variables['npv']}
• Payback Period: {variables['payback_period']}
• DSCR (Average): 1.35x
• Peak Annual Cash Flow: Year 8-15
• Cumulative Cash Flow Positive: Year 9""",

        'roi_analysis': f"""Return on Investment

• Project IRR: {variables['irr']}
• Equity IRR: 15.8%
• NPV @ 10%: {variables['npv']}
• ROI Metrics exceed industry benchmarks
• Payback Period: {variables['payback_period']}
• Risk-adjusted returns competitive""",

        'sensitivity_analysis': f"""Sensitivity Analysis

• Energy Price ±10%: IRR range 10.2% - 14.8%
• CapEx ±10%: IRR range 10.8% - 14.2%
• Capacity Factor ±5%: IRR range 11.1% - 13.9%
• O&M Costs ±20%: IRR range 12.1% - 12.9%
• All scenarios maintain positive NPV
• Base case IRR: {variables['irr']}""",

        'financing_structure': f"""Financing Structure

• Total Project Cost: {variables['project_cost']}
• Debt Financing: 70% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.7 / 1000000:.1f}M)
• Equity Investment: 30% ({float(variables['project_cost'].replace('$', '').replace(',', '')) * 0.3 / 1000000:.1f}M)
• Debt Term: 18 years
• Interest Rate: 4.5% (fixed)
• DSCR Covenant: >1.20x""",

        # Appendix
        'supporting_docs': f"""Supporting Documentation

• Technical Studies: Feasibility, interconnection
• Financial Models: 25-year cash flow model
• Legal Documents: Land lease, permits
• Environmental Studies: Impact assessment
• Third-party Reports: Technical due diligence
• Insurance Documentation: Construction & operational""",

        'technical_drawings': f"""Technical Drawings and Schematics

• Site Plan: {variables['capacity']} layout design
• System Architecture: Single-line diagrams
• Electrical Schematics: Grid interconnection
• Equipment Specifications: Detailed datasheets
• Installation Details: Foundation, mounting
• As-built Drawings: Post-construction""",

        'regulatory_compliance': f"""Regulatory Compliance

• Environmental Permits: Approved
• Building Permits: In process
• Grid Interconnection: Study complete
• Safety Certifications: Equipment certified
• Local Approvals: Zoning, setbacks
• Compliance Timeline: Q2 {variables['date'].split()[-1]}""",

        'environmental_impact': f"""Environmental Impact Assessment

• Environmental Screening: Completed
• Habitat Assessment: No critical habitats
• Visual Impact: Minimal due to location
• Noise Assessment: <45dB at property line
• Mitigation Measures: Native vegetation restoration
• Monitoring: Annual environmental reports""",

        'contact_info': f"""Contact Information and References

• Project Manager: John Smith, jsmith@{variables['company_name'].lower().replace(' ', '')}.com, (555) 123-4567
• Technical Lead: Sarah Johnson, sjohnson@{variables['company_name'].lower().replace(' ', '')}.com, (555) 123-4568
• Financial Lead: Mike Chen, mchen@{variables['company_name'].lower().replace(' ', '')}.com, (555) 123-4569
• Legal Counsel: Anderson & Associates, legal@anderson.com, (555) 123-4570
• EPC Contractor: [To be determined]"""
    }
    
    # Get content template based on slide template file name
    template_key = slide_id or slide_config['section']
    return content_templates.get(template_key, f"Template content for {slide_config['title']}")

def apply_slide_formatting(slide, section):
    """
    Apply section-specific formatting to slides
    """
    try:
        # Apply different formatting based on section
        if section == 'title':
            # Title slide formatting
            if slide.shapes.title:
                title_format = slide.shapes.title.text_frame.paragraphs[0].font
                title_format.size = Pt(28)
                title_format.bold = True
        
        elif section in ['economics-finance', 'module-procurement']:
            # Financial slides - make numbers stand out
            if len(slide.placeholders) > 1:
                content_format = slide.placeholders[1].text_frame.paragraphs[0].font
                content_format.size = Pt(16)
        
        # Add more formatting rules as needed
        
    except Exception as e:
        print(f"Warning: Could not apply formatting to {section}: {str(e)}")
        # Continue without failing the entire process

# --- Template Version 2: Dynamic PPTX Slide Customization ---
@app.route('/template_v2')
def template_v2():
    # Render the new tab with purple color scheme
    return render_template('template_v2.html', color_scheme='purple')

@app.route('/api/template_v2/<template>', methods=['GET'])
def get_template_v2_map(template):
    map_file = os.path.join(TEMPLATE_V2_DIR, f"{template}.map.json")
    if not os.path.exists(map_file):
        return {"error": "Mapping not found."}, 404
    return send_file(map_file, mimetype='application/json')

@app.route('/api/render_slide_v2', methods=['POST'])
def render_slide_v2():
    req = request.get_json()
    pptx_path = os.path.join(TEMPLATE_V2_DIR, f"{req['template']}.pptx")
    if not inject_text:
        return {"error": "Backend not fully implemented."}, 500
    out_pptx = inject_text(pptx_path, req['updates'])
    return send_file(out_pptx, as_attachment=True, download_name=f"{req['template']}_custom.pptx")

if __name__ == '__main__':
    app.run(debug=True) 