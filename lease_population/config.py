"""
Configuration settings for lease population module
"""

# Image processing settings
IMAGE_SETTINGS = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'max_width_inches': 6.0,
    'supported_formats': ['image/png', 'image/jpeg', 'image/jpg'],
    'default_format': 'PNG'
}

# Document processing settings
DOCUMENT_SETTINGS = {
    'word_version': '16.0',
    'last_modified_by': 'Document Processor',
    'track_changes_highlight_color': 7  # yellow
}

# Placeholder settings
PLACEHOLDER_SETTINGS = {
    'image_placeholders': ['[image]', '[image_1]', '[image_2]', '[exhibit_a_image_1]'],
    'signature_placeholders': ['[Signature Block]', '[Notary Block]'],
    'bracket_removal': True
} 