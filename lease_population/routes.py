"""
Route handlers for lease population functionality
"""

from flask import request, jsonify
from .core import LeasePopulationProcessor


def register_lease_population_routes(app):
    """Register all lease population routes with the Flask app"""
    
    processor = LeasePopulationProcessor()
    
    @app.route('/lease_population_replace', methods=['POST'])
    def lease_population_replace():
        """Main lease population replacement route"""
        try:
            if 'docx' not in request.files or 'mapping' not in request.form:
                return jsonify({'error': 'Missing file or mapping'}), 400
            
            print(f"[DEBUG] Request content length: {request.content_length}")
            print(f"[DEBUG] Request content type: {request.content_type}")
            
            docx_file = request.files['docx']
            mapping_json = request.form['mapping']
            track_changes = request.form.get('track_changes', 'false').lower() == 'true'
            document_name = request.form.get('document_name', 'lease_population_filled')
            image_file = request.files.get('exhibit_image')
            
            print(f"[DEBUG] Processing document: {document_name}")
            print(f"[DEBUG] Track changes: {track_changes}")
            print(f"[DEBUG] Image file present: {bool(image_file)}")
            
            return processor.process_lease_population(
                docx_file=docx_file,
                mapping_json=mapping_json,
                track_changes=track_changes,
                document_name=document_name,
                image_file=image_file
            )
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"CRITICAL ERROR in lease_population_replace: {str(e)}")
            print(f"TRACEBACK: {error_traceback}")
            return jsonify({'error': f'Critical error: {str(e)}', 'traceback': error_traceback}), 500
    
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