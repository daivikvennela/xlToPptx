# PNG Image Embedding in DOCX Documents

## Overview

This system provides robust PNG image embedding functionality for legal documents (lease agreements, easements, etc.) by replacing `[EXHIBIT_A_IMAGE_1]` placeholders with properly sized and centered images.

## Features

- ✅ **PNG-only support** with comprehensive validation
- ✅ **Automatic image resizing** (max 6 inches width)
- ✅ **Transparency handling** (converts to RGB with white background)
- ✅ **Centered image placement** in documents
- ✅ **Large file support** (up to 50MB)
- ✅ **Comprehensive error handling** and logging
- ✅ **Production-ready** with extensive testing

## Workflow

### 1. Frontend (JavaScript)

```javascript
// Upload PNG image
const fileInput = document.getElementById('exhibitImageInput');
fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file && file.type === 'image/png') {
        exhibitImage = file;
    }
});

// Generate Exhibit A with image
async function generateExhibitString() {
    const formData = new FormData();
    formData.append('parcels', JSON.stringify(parcelList));
    formData.append('image', exhibitImage); // Send original PNG file
    
    const response = await fetch('/gen_exhibit_a', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    exhibitString = data.exhibit_string; // Contains [EXHIBIT_A_IMAGE_1] placeholder
    exhibitAImage1 = data.exhibit_a_image_1; // Base64 image data
}
```

### 2. Backend Processing

```python
# In gen_exhibit_a route
if image_file:
    # Validate PNG file
    if not image_file.filename.lower().endswith('.png'):
        return jsonify({'error': 'Only PNG files are supported'}), 400
    
    # Validate PNG header
    image_data = image_file.read()
    if not image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return jsonify({'error': 'Invalid PNG file'}), 400
    
    # Convert to base64
    img_b64 = base64.b64encode(image_data).decode('utf-8')
    exhibit_a_image_1 = img_b64

# Generate exhibit string with placeholder
exhibit_string = build_exhibit_string(parcels, img_b64, ...)
# Returns: "EXHIBIT A\n\n[EXHIBIT_A_IMAGE_1]\n\nParcel 1: ..."
```

### 3. Document Processing

```python
# In lease_population_replace route
if exhibit_a_image_1:
    # Embed image BEFORE text replacement
    success = embedImage(doc, exhibit_a_image_1, '[EXHIBIT_A_IMAGE_1]')
    if success:
        # Remove from text replacement mapping
        del mapping['[EXHIBIT_A_IMAGE_1]']

# Process remaining text placeholders
doc = replace_placeholders_in_docx(doc, mapping)
```

## Image Embedding Function

### Core Function: `embedImage()`

```python
def embedImage(doc: Document, image_data: str, placeholder: str = '[EXHIBIT_A_IMAGE_1]'):
    """
    Embeds PNG image into DOCX document at placeholder location.
    
    Args:
        doc: DOCX document object
        image_data: Base64 encoded PNG string
        placeholder: Text placeholder to replace
    
    Returns:
        bool: True if successful, False otherwise
    """
```

### Key Features:

1. **PNG Validation**: Checks file header and format
2. **Image Processing**: Converts transparency to RGB with white background
3. **Resizing**: Automatically resizes to max 6 inches width
4. **Placement**: Centers image in paragraph
5. **Error Handling**: Comprehensive logging and graceful failures

## Template Usage

### Adding Image Placeholder to DOCX

1. **Open your DOCX template**
2. **Add placeholder text**: `[EXHIBIT_A_IMAGE_1]`
3. **Position as needed**: The image will replace this text and be centered
4. **Save template**: The system will find and replace this placeholder

### Example Template Structure

```
EXHIBIT A

[EXHIBIT_A_IMAGE_1]

Parcel 1: Legal description...
Parcel 2: Legal description...
```

## API Endpoints

### `/gen_exhibit_a` (POST)
- **Purpose**: Generate Exhibit A with image placeholder
- **Input**: PNG file + parcels data
- **Output**: Exhibit string + base64 image data

### `/lease_population_replace` (POST)
- **Purpose**: Process document with image embedding
- **Input**: DOCX file + mapping + image data
- **Output**: Processed DOCX with embedded image

### `/test_image_embedding_comprehensive` (POST)
- **Purpose**: Test image embedding functionality
- **Input**: Test PNG files
- **Output**: Test results and validation

## Error Handling

### Common Errors and Solutions

1. **"Only PNG files are supported"**
   - **Cause**: Non-PNG file uploaded
   - **Solution**: Use PNG format only

2. **"Invalid PNG file: incorrect header"**
   - **Cause**: Corrupted or invalid PNG
   - **Solution**: Use valid PNG file

3. **"Image file too large"**
   - **Cause**: File exceeds 50MB limit
   - **Solution**: Compress or resize image

4. **"Placeholder not found in document"**
   - **Cause**: `[EXHIBIT_A_IMAGE_1]` missing from template
   - **Solution**: Add placeholder to DOCX template

## Testing

### Manual Testing

1. **Valid PNG Test**:
   ```bash
   curl -X POST -F "valid_png=@test.png" http://localhost:5000/test_image_embedding_comprehensive
   ```

2. **Invalid File Test**:
   ```bash
   curl -X POST -F "invalid_file=@test.jpg" http://localhost:5000/test_image_embedding_comprehensive
   ```

3. **Missing Placeholder Test**:
   ```bash
   curl -X POST -F "missing_placeholder=@test.png" http://localhost:5000/test_image_embedding_comprehensive
   ```

### Automated Testing

The system includes comprehensive test coverage for:
- ✅ Valid PNG processing
- ✅ Invalid file rejection
- ✅ Missing placeholder handling
- ✅ Large file processing
- ✅ Transparency conversion
- ✅ Image resizing
- ✅ Document formatting preservation

## Troubleshooting

### Debug Logs

Enable debug logging to track issues:

```python
# In app.py
print(f"[DEBUG] Image data size: {len(image_data)} bytes")
print(f"[DEBUG] Base64 size: {len(img_b64)} characters")
print(f"[DEBUG] Embedding success: {success}")
```

### Common Issues

1. **Image not appearing**: Check if placeholder exists in template
2. **Large file errors**: Verify file size limits
3. **Format issues**: Ensure PNG format and valid header
4. **Processing errors**: Check server logs for detailed error messages

## Performance Considerations

- **File Size**: Maximum 50MB PNG files
- **Processing Time**: Large images may take 10-30 seconds
- **Memory Usage**: Base64 encoding increases size by ~33%
- **Document Size**: Embedded images increase DOCX file size

## Security Considerations

- **File Validation**: PNG header and MIME type checking
- **Size Limits**: Prevents DoS attacks with large files
- **Error Handling**: No sensitive data in error messages
- **Input Sanitization**: All inputs validated before processing

## Maintenance

### Adding New Image Placeholders

1. **Update template**: Add new placeholder (e.g., `[EXHIBIT_A_IMAGE_2]`)
2. **Update frontend**: Add corresponding image handling
3. **Update backend**: Add to mapping processing
4. **Test thoroughly**: Verify embedding works correctly

### Modifying Image Processing

1. **Size limits**: Adjust `max_width_inches` in `embedImage()`
2. **Format support**: Add new formats to validation
3. **Quality settings**: Modify Pillow save parameters
4. **Background color**: Change RGB values for transparency handling

## Dependencies

- **Flask**: Web framework
- **python-docx**: DOCX document processing
- **Pillow**: Image processing and manipulation
- **base64**: Image data encoding/decoding

## License

This implementation is part of the xlToPPtx project and follows the same licensing terms.
