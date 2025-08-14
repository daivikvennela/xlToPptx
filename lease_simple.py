"""
Single-file Lease (Simple) flow.

Accepts JSON + DOCX (and optional parcels) and returns the processed DOCX.
"""

from flask import request, jsonify
import json as _json


def _parse_json_file(json_file_storage):
    """Parse uploaded JSON file into list[{key,value}]"""
    try:
        text = json_file_storage.read().decode('utf-8')
    except Exception:
        # Some browsers provide str bytes already
        text = json_file_storage.read()
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='ignore')
    data = _json.loads(text)
    mapping = []
    if isinstance(data, list):
        # Expect list of {key, value}
        mapping = [
            {"key": str(item.get("key", "")).strip(), "value": str(item.get("value", ""))}
            for item in data
            if isinstance(item, dict) and str(item.get("key", "")).strip() != ""
        ]
    elif isinstance(data, dict):
        mapping = [{"key": str(k), "value": str(v)} for k, v in data.items()]
    else:
        raise ValueError("Unsupported JSON format; expected object or array of {key,value}")
    return mapping


def _inject_exhibit_a(mapping_list, parcels):
    """Inject Exhibit A text under [EXHIBIT A] given an array of parcel descriptions (no portions)."""
    if not parcels:
        return mapping_list
    header = "EXHIBIT A"
    body = "\n\n".join([f"Parcel {i+1}:\n{p}" for i, p in enumerate(parcels) if str(p).strip()])
    exhibit = f"{header}\n\n{body}" if body else header
    key = "[EXHIBIT A]"
    # Replace or append
    for item in mapping_list:
        if item.get("key", "").strip().lower() == key.lower():
            item["value"] = exhibit
            break
    else:
        mapping_list.append({"key": key, "value": exhibit})
    return mapping_list


def register_lease_simple_routes(app):
    @app.route('/lease_simple', methods=['POST'])
    def lease_simple():
        try:
            if 'docx' not in request.files or ('json' not in request.files and 'json_file' not in request.files):
                return jsonify({'error': 'Missing DOCX or JSON file'}), 400

            docx_file = request.files['docx']
            json_file = request.files.get('json') or request.files.get('json_file')

            # Parse mapping from JSON file
            mapping_list = _parse_json_file(json_file)

            # Optional parcels (as JSON list or plain text lines)
            parcels = []
            if 'parcels' in request.form:
                try:
                    parcels_data = request.form.get('parcels', '').strip()
                    if parcels_data.startswith('['):
                        parcels = _json.loads(parcels_data)
                    else:
                        parcels = [line for line in parcels_data.split('\n') if line.strip()]
                except Exception:
                    parcels = []

            mapping_list = _inject_exhibit_a(mapping_list, parcels)

            # Build mapping_json string for existing processor
            mapping_json = _json.dumps(mapping_list)

            # Optional flags/args
            track_changes = request.form.get('track_changes', 'false').lower() == 'true'
            document_name = request.form.get('document_name', 'lease_population_filled')

            # Reuse existing processor
            from lease_population.core import LeasePopulationProcessor
            processor = LeasePopulationProcessor()
            return processor.process_lease_population(
                docx_file=docx_file,
                mapping_json=mapping_json,
                track_changes=track_changes,
                document_name=document_name,
            )

        except Exception as e:
            import traceback
            return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


