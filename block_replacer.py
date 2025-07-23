# block_replacer.py

import os
from docx import Document

def load_block_template(filename):
    path = os.path.join('templates', 'blocks', filename)
    with open(path, 'r') as f:
        return f.read()

def generate_signature_block(grantor_name, trust_entity_name=None, name=None, title=None, block_type='individual', state=None, county=None, name_of_individuals=None, type_of_authority=None, instrument_for=None):
    if block_type == 'individual':
        template = load_block_template('individual_signature.txt')
        return template.replace('[Grantor Name]', grantor_name or '')
    else:
        template = load_block_template('entity_signature.txt')
        return template.replace('[Trust/Entity Name]', trust_entity_name or '') \
                      .replace('[Name]', name or '') \
                      .replace('[Title]', title or '')

def generate_notary_block(state, county, name_of_individuals, type_of_authority=None, instrument_for=None, block_type='individual'):
    if block_type == 'individual':
        template = load_block_template('individual_notary.txt')
        return template.replace('[State]', state or '') \
                      .replace('[County]', county or '') \
                      .replace('[NAME(S) OF INDIVIDUAL(S)]', name_of_individuals or '')
    else:
        template = load_block_template('entity_notary.txt')
        return template.replace('[State]', state or '') \
                      .replace('[County]', county or '') \
                      .replace('[NAME(S) OF INDIVIDUAL(S)]', name_of_individuals or '') \
                      .replace('[TYPE OF AUTHORITY]', type_of_authority or '') \
                      .replace('[NAME OF ENTITY OR TRUST WHOM INSTRUMENT WAS EXECUTED FOR]', instrument_for or '')

def get_all_block_previews(grantor_name, trust_entity_name, name, title, state, county, name_of_individuals, type_of_authority, instrument_for):
    preview = {
        'individual_signature': generate_signature_block(grantor_name, block_type='individual'),
        'individual_notary': generate_notary_block(state, county, name_of_individuals, block_type='individual'),
        'entity_signature': generate_signature_block(grantor_name, trust_entity_name, name, title, block_type='entity'),
        'entity_notary': generate_notary_block(state, county, name_of_individuals, type_of_authority, instrument_for, block_type='entity'),
    }
    return preview

def replace_signature_and_notary_blocks(doc: Document, mapping: dict):
    # Determine party type (robust: use [Grantor Type] if present, fallback to [Grantee Type])
    party_type = mapping.get('[Grantor Type]', '').strip().lower() or mapping.get('[Grantee Type]', '').strip().lower()
    is_individual = party_type in ('individual', 'i')
    # Prepare values for template filling
    grantor_name = mapping.get('[Grantor Name]', '')
    trust_entity_name = mapping.get('[Trust/Entity Name]', '')
    name = mapping.get('[Name]', '')
    title = mapping.get('[Title]', '')
    state = mapping.get('[State]', '')
    county = mapping.get('[County]', '')
    name_of_individuals = mapping.get('[NAME(S) OF INDIVIDUAL(S)]', '')
    type_of_authority = mapping.get('[TYPE OF AUTHORITY]', '')
    instrument_for = mapping.get('[NAME OF ENTITY OR TRUST WHOM INSTRUMENT WAS EXECUTED FOR]', '')
    # Generate blocks
    if is_individual:
        sig_block = generate_signature_block(grantor_name, block_type='individual')
        notary_block = generate_notary_block(state, county, name_of_individuals, block_type='individual')
    else:
        sig_block = generate_signature_block(grantor_name, trust_entity_name, name, title, block_type='entity')
        notary_block = generate_notary_block(state, county, name_of_individuals, type_of_authority, instrument_for, block_type='entity')
    # Replace placeholders in the document
    for paragraph in doc.paragraphs:
        if '[Signature Block]' in paragraph.text:
            paragraph.text = paragraph.text.replace('[Signature Block]', sig_block)
        if '[Notary Block]' in paragraph.text:
            paragraph.text = paragraph.text.replace('[Notary Block]', notary_block)
    # Also replace in tables, headers, footers, and footnotes if needed
    def process_block(block):
        for paragraph in block.paragraphs:
            if '[Signature Block]' in paragraph.text:
                paragraph.text = paragraph.text.replace('[Signature Block]', sig_block)
            if '[Notary Block]' in paragraph.text:
                paragraph.text = paragraph.text.replace('[Notary Block]', notary_block)
        for table in getattr(block, 'tables', []):
            for row in table.rows:
                for cell in row.cells:
                    process_block(cell)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                process_block(cell)
    for section in doc.sections:
        process_block(section.header)
        process_block(section.footer)
    if hasattr(doc, 'part') and hasattr(doc.part, 'footnotes'):
        for footnote in doc.part.footnotes.part.footnotes:
            for paragraph in footnote.paragraphs:
                if '[Signature Block]' in paragraph.text:
                    paragraph.text = paragraph.text.replace('[Signature Block]', sig_block)
                if '[Notary Block]' in paragraph.text:
                    paragraph.text = paragraph.text.replace('[Notary Block]', notary_block)
    return doc 