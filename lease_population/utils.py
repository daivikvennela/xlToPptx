"""
Utility functions for lease population processing
"""


def normalize_placeholder_key(key):
    """Return only the key as-is for direct matching (no variants)."""
    return [key.strip()]


def strip_brackets(placeholder):
    """Remove surrounding brackets from a placeholder if present."""
    s = placeholder.strip()
    if s.startswith('[') and s.endswith(']'):
        return s[1:-1].strip()
    return s


def parse_kv_table_file(file_storage):
    """Parse key-value table file and return mapping"""
    try:
        content = file_storage.read().decode('utf-8')
        lines = content.strip().split('\n')
        mapping = []
        
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                mapping.append({'key': key.strip(), 'value': value.strip()})
        
        return mapping
    except Exception as e:
        print(f"Error parsing KV table file: {str(e)}")
        return [] 