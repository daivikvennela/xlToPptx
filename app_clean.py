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
from flask import request, jsonify
from lease_population.block_replacer import get_all_block_previews
from lease_population.block_replacer import replace_signature_and_notary_blocks
from docx import Document
from lease_population.block_replacer import generate_signature_block, generate_notary_block
from lease_population.block_replacer import getSigBlock, getNotaryBlock, generate_enhanced_combined_block

# --- Lease Population Module Integration ---
from lease_population import register_lease_population_routes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = None  # No size limit
app.config['MAX_CONTENT_PATH'] = None  # No path length limit
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No caching for large files

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register lease population routes
register_lease_population_routes(app)

# --- Essential Routes for Lease Population ---

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/parse_kv_table', methods=['POST'])
def parse_kv_table():
    """Parse key-value table from uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file.filename.endswith('.csv'):
            content = file.read().decode('utf-8')
            reader = csv.reader(content.splitlines())
            rows = list(reader)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file, header=None)
            rows = df.values.tolist()
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Convert to key-value pairs
        kv_pairs = []
        document_name = 'lease_population_filled'
        
        if rows:
            document_name = rows[0][0].strip() if rows[0] and rows[0][0] else 'lease_population_filled'
        
        for row in rows[1:]:  # Skip first row (document name)
            if len(row) >= 2 and row[0] and row[1]:
                kv_pairs.append({
                    'key': str(row[0]).strip(),
                    'value': str(row[1]).strip()
                })
        
        return jsonify({
            'kv_pairs': kv_pairs,
            'document_name': document_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/block_preview', methods=['POST'])
def block_preview():
    data = request.get_json()
    grantor_name = data.get('grantor_name', '')
    trust_entity_name = data.get('trust_entity_name', '')
    name = data.get('name', '')
    title = data.get('title', '')
    state = data.get('state', '')
    county = data.get('county', '')
    name_of_individuals = data.get('name_of_individuals', '')
    type_of_authority = data.get('type_of_authority', '')
    instrument_for = data.get('instrument_for', '')
    preview = get_all_block_previews(
        grantor_name, trust_entity_name, name, title, state, county, name_of_individuals, type_of_authority, instrument_for
    )
    return jsonify(preview)

@app.route('/get_dynamic_block_preview', methods=['POST'])
def get_dynamic_block_preview():
    """Enhanced endpoint for dynamic signature/notary block preview with embedding logic"""
    try:
        data = request.get_json()
        owner_type = data.get('owner_type', 'individual')
        num_signatures = data.get('num_signatures', 1)
        
        try:
            num_signatures = int(num_signatures)
        except (ValueError, TypeError):
            num_signatures = 1
        
        include_signature = data.get('include_signature', True)
        include_notary = data.get('include_notary', True)
        embed_notary_in_signature = data.get('embed_notary_in_signature', True)
        
        from lease_population.block_replacer import generate_enhanced_combined_block
        
        combined_block = generate_enhanced_combined_block(
            owner_type=owner_type,
            num_signatures=num_signatures,
            include_signature=include_signature,
            include_notary=include_notary,
            embed_notary_in_signature=embed_notary_in_signature
        )
        
        return jsonify({'combined_block': combined_block})
        
    except Exception as e:
        print(f"Error in get_dynamic_block_preview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_party_block_templates', methods=['POST'])
def get_party_block_templates():
    """Get party-specific block templates"""
    try:
        data = request.get_json()
        party_type = data.get('party_type', 'individual')
        base = 'templates/blocks'
        
        if party_type == 'individual':
            sig_file = os.path.join(base, 'individual_signature.txt')
            notary_file = os.path.join(base, 'individual_notary.txt')
        else:
            sig_file = os.path.join(base, 'entity_signature.txt')
            notary_file = os.path.join(base, 'entity_notary.txt')
        
        with open(sig_file, 'r') as f:
            sig_block = f.read()
        with open(notary_file, 'r') as f:
            notary_block = f.read()
        return jsonify({'signature_block': sig_block, 'notary_block': notary_block})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_signature_block', methods=['POST'])
def generate_signature_block():
    """
    Generate signature block using the generator function
    """
    try:
        data = request.get_json()
        owner_type = data.get('ownerType', 'individual')
        is_notary = data.get('isNotary', False)
        num_signatures = int(data.get('numSignatures', 1))
        
        print(f"[DEBUG] Generating signature block: owner_type='{owner_type}', is_notary={is_notary}, num_signatures={num_signatures}")
        
        # Validate number of signatures
        if num_signatures < 1:
            return jsonify({'success': False, 'error': 'Number of signatures must be at least 1'}), 400
        
        # Import and use the generator function
        from lease_population.block_replacer import generator
        
        # Call generator with the new signature
        result = generator(owner_type, is_notary, '', num_signatures)
        print(f"[DEBUG] Generated content length: {len(result)}")
        return jsonify({'success': True, 'content': result})
        
    except Exception as e:
        print(f"[ERROR] Error generating signature block: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_signature_block', methods=['POST'])
def get_signature_block():
    data = request.get_json()
    owner_type = data.get('ownerType', 'individual')
    num_signatures = data.get('numSignatures', 1)
    try:
        num_signatures = int(num_signatures)
    except:
        num_signatures = 1
    content = getSigBlock(owner_type, num_signatures)
    return jsonify({'signature_block': content})

@app.route('/get_notary_block', methods=['POST'])
def get_notary_block():
    content = getNotaryBlock()
    return jsonify({'notary_block': content})

@app.route('/gen_exhibit_a', methods=['POST'])
def gen_exhibit_a():
    """
    Generate Exhibit A string from parcels, image, and description templates.
    """
    try:
        data = request.get_json()
        parcels = data.get('parcels', [])
        
        if not parcels:
            return jsonify({
                'success': False,
                'error': 'No parcels provided'
            }), 400
        
        # Validate parcels structure
        for i, parcel in enumerate(parcels):
            if not isinstance(parcel, dict):
                return jsonify({
                    'success': False,
                    'error': f'Parcel {i+1} is not a valid object'
                }), 400
        
        print(f"[DEBUG] Processing {len(parcels)} parcels for Exhibit A generation")
        
        # Generate exhibit string using the build_exhibit_string function
        try:
            from lease_population.block_replacer import build_exhibit_string
            exhibit_string = build_exhibit_string(parcels)
            print(f"[DEBUG] Generated exhibit string, length: {len(exhibit_string)}")
            return jsonify({
                'success': True,
                'exhibit_string': exhibit_string,
                'parcel_count': len(parcels)
            })
        except Exception as e:
            print(f"[ERROR] Failed to generate exhibit string: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to generate exhibit string: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"[ERROR] Error in gen_exhibit_a: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_image_embedding', methods=['POST'])
def test_image_embedding():
    """Test image embedding functionality"""
    try:
        if 'docx_file' not in request.files or 'image_file' not in request.files:
            return jsonify({'error': 'Missing DOCX or image file'}), 400
        
        docx_file = request.files['docx_file']
        image_file = request.files['image_file']
        
        if not docx_file.filename.lower().endswith('.docx'):
            return jsonify({'error': 'Invalid DOCX file'}), 400
        
        # Read image data and convert to base64
        image_data = image_file.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Load document
        doc = Document(docx_file)
        
        # Test image embedding
        from lease_population.block_replacer import embedImage
        success = embedImage(doc, image_b64, '[EXHIBIT_A_IMAGE_1]')
        
        if success:
            # Save and return the document
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name='test_image_embedded.docx'
            )
        else:
            return jsonify({'error': 'Image embedding failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_image_embedding_comprehensive', methods=['POST'])
def test_image_embedding_comprehensive():
    """Comprehensive test for image embedding with multiple formats and validation"""
    try:
        if 'docx_file' not in request.files or 'image_file' not in request.files:
            return jsonify({'error': 'Missing DOCX or image file'}), 400
        
        docx_file = request.files['docx_file']
        image_file = request.files['image_file']
        
        # Validate files
        if not docx_file.filename.lower().endswith('.docx'):
            return jsonify({'error': 'Invalid DOCX file'}), 400
        
        # Read and validate image
        image_data = image_file.read()
        
        # Basic image validation
        try:
            image = Image.open(io.BytesIO(image_data))
            image_format = image.format
            image_size = image.size
            image_mode = image.mode
        except Exception as e:
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400
        
        # Convert to RGB if necessary
        if image_mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image_size, (255, 255, 255))
            if image_mode == 'P':
                image = image.convert('RGBA')
            if image_mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            image = background
        elif image_mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to PNG and base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG', optimize=True)
        image_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # Load document
        doc = Document(docx_file)
        
        # Test image embedding
        from lease_population.block_replacer import embedImage
        success = embedImage(doc, image_b64, '[EXHIBIT_A_IMAGE_1]')
        
        if success:
            # Save and return the document
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name='test_comprehensive_image_embedded.docx'
            )
        else:
            return jsonify({'error': 'Image embedding failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)