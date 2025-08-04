"""
Enhanced route handlers for lease population functionality
"""

from flask import request, jsonify, send_file
from .core import LeasePopulationProcessor
import logging

logger = logging.getLogger(__name__)


def register_lease_population_routes(app):
    """Register all lease population routes with the Flask app"""
    
    processor = LeasePopulationProcessor()
    
    @app.route('/lease_population_replace', methods=['POST'])
    def lease_population_replace():
        """Main lease population replacement route with enhanced image support"""
        try:
            if 'docx' not in request.files or 'mapping' not in request.form:
                return jsonify({'error': 'Missing file or mapping'}), 400
            
            logger.info(f"Request content length: {request.content_length}")
            logger.info(f"Request content type: {request.content_type}")
            
            docx_file = request.files['docx']
            mapping_json = request.form['mapping']
            track_changes = request.form.get('track_changes', 'false').lower() == 'true'
            document_name = request.form.get('document_name', 'lease_population_filled')
            
            # Enhanced image handling
            image_files = {}
            watermark_text = request.form.get('watermark_text', '').strip()
            target_format = request.form.get('image_format', 'PNG').upper()
            
            # Process multiple image files
            for key in request.files:
                if key.startswith('image_') or key == 'exhibit_image':
                    image_files[key] = request.files[key]
                    logger.info(f"Found image file: {key} - {image_files[key].filename}")
            
            logger.info(f"Processing document: {document_name}")
            logger.info(f"Track changes: {track_changes}")
            logger.info(f"Image files found: {len(image_files)}")
            logger.info(f"Watermark text: {watermark_text}")
            logger.info(f"Target format: {target_format}")
            
            return processor.process_lease_population_enhanced(
                docx_file=docx_file,
                mapping_json=mapping_json,
                track_changes=track_changes,
                document_name=document_name,
                image_files=image_files,
                watermark_text=watermark_text,
                target_format=target_format
            )
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"CRITICAL ERROR in lease_population_replace: {str(e)}")
            logger.error(f"TRACEBACK: {error_traceback}")
            return jsonify({'error': f'Critical error: {str(e)}', 'traceback': error_traceback}), 500
    
    @app.route('/image/validate', methods=['POST'])
    def validate_image():
        """Validate image file before processing"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file uploaded'}), 400
            
            image_file = request.files['image']
            image_data = image_file.read()
            
            # Use the enhanced image handler for validation
            from .image_handler import ImageEmbeddingHandler
            handler = ImageEmbeddingHandler()
            
            is_valid, format_name, error_msg = handler.validate_image_file(image_data)
            
            if is_valid:
                return jsonify({
                    'valid': True,
                    'format': format_name,
                    'size': len(image_data),
                    'message': f'Valid {format_name} image ({len(image_data)} bytes)'
                })
            else:
                return jsonify({
                    'valid': False,
                    'error': error_msg
                }), 400
                
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            return jsonify({'error': f'Validation failed: {str(e)}'}), 500
    
    @app.route('/image/preview', methods=['POST'])
    def preview_image():
        """Generate preview of image with watermark and optimization"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file uploaded'}), 400
            
            image_file = request.files['image']
            watermark_text = request.form.get('watermark_text', '').strip()
            target_format = request.form.get('format', 'PNG').upper()
            
            # Process image for preview
            from .image_handler import ImageEmbeddingHandler
            handler = ImageEmbeddingHandler()
            
            image_data = image_file.read()
            image = handler.optimize_image(image_data, target_format)
            
            if watermark_text:
                image = handler.add_watermark(image, watermark_text)
            
            # Convert back to base64 for preview
            import base64
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=target_format)
            preview_data = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'preview_data': f'data:image/{target_format.lower()};base64,{preview_data}',
                'format': target_format,
                'size': len(img_byte_arr.getvalue())
            })
            
        except Exception as e:
            logger.error(f"Image preview error: {str(e)}")
            return jsonify({'error': f'Preview generation failed: {str(e)}'}), 500
    
    @app.route('/image/batch_process', methods=['POST'])
    def batch_process_images():
        """Process multiple images in batch"""
        try:
            if 'docx' not in request.files:
                return jsonify({'error': 'No document file uploaded'}), 400
            
            docx_file = request.files['docx']
            image_mappings = request.form.get('image_mappings', '[]')
            
            try:
                import json
                mappings = json.loads(image_mappings)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid image mappings JSON'}), 400
            
            # Process document with batch image embedding
            from .image_handler import ImageEmbeddingHandler
            from docx import Document
            
            handler = ImageEmbeddingHandler()
            doc = Document(docx_file)
            
            results = handler.batch_process_images(doc, mappings)
            
            # Save processed document
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                doc.save(tmp_file.name)
                output_path = tmp_file.name
            
            return jsonify({
                'success': True,
                'results': results,
                'output_path': output_path
            })
            
        except Exception as e:
            logger.error(f"Batch image processing error: {str(e)}")
            return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500
    
    @app.route('/test_party_type', methods=['POST'])
    def test_party_type():
        """Test party type functionality"""
        if 'docx' not in request.files or 'mapping' not in request.form:
            return jsonify({'error': 'Missing file or mapping'}), 400
        
        docx_file = request.files['docx']
        mapping_json = request.form['mapping']
        party_type = request.form.get('party_type', '').strip()
        document_name = request.form.get('document_name', 'party_type_test')
        
        return processor.test_party_type(
            docx_file=docx_file,
            mapping_json=mapping_json,
            party_type=party_type,
            document_name=document_name
        )
    
    @app.route('/image/supported_formats', methods=['GET'])
    def get_supported_formats():
        """Get list of supported image formats"""
        from .image_handler import ImageEmbeddingHandler
        handler = ImageEmbeddingHandler()
        
        return jsonify({
            'supported_formats': list(handler.supported_formats.keys()),
            'max_file_size_mb': handler.max_file_size // (1024 * 1024),
            'max_width_inches': handler.max_width_inches,
            'quality_settings': handler.quality_settings
        }) 