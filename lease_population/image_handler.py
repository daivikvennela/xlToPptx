"""
Image handling functionality for lease population
"""

import base64
import io
from PIL import Image
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


class ImageEmbeddingHandler:
    """Handles image embedding functionality"""
    
    def embed_image_enhanced(self, doc: Document, image_data: str, placeholder: str):
        """Enhanced image embedding with better error handling and multi-format support"""
        try:
            print(f"[DEBUG] Starting enhanced image embedding for placeholder: {placeholder}")
            
            # Validate input
            if not image_data or not isinstance(image_data, str):
                print("[ERROR] Invalid image data: must be non-empty string")
                return False
            
            # Decode base64 image data
            try:
                image_bytes = base64.b64decode(image_data)
                print(f"[DEBUG] Decoded base64 image data, size: {len(image_bytes)} bytes")
            except Exception as e:
                print(f"[ERROR] Failed to decode base64 image data: {str(e)}")
                return False
            
            # Enhanced validation
            if len(image_bytes) < 8:
                print("[ERROR] Image data too small to be valid")
                return False
            
            # Support multiple image formats
            valid_headers = [
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'\xff\xd8\xff',        # JPEG
            ]
            
            if not any(image_bytes.startswith(header) for header in valid_headers):
                print("[ERROR] Invalid image format - only PNG and JPEG supported")
                return False
            
            # Process image with Pillow
            try:
                image = Image.open(io.BytesIO(image_bytes))
                print(f"[DEBUG] Opened image: format={image.format}, size={image.size}, mode={image.mode}")
                
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                    print("[DEBUG] Converted transparent image to RGB with white background")
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                    print(f"[DEBUG] Converted image from {image.mode} to RGB")
            except Exception as e:
                print(f"[ERROR] Failed to process image with Pillow: {str(e)}")
                return False
            
            # Enhanced resizing with better proportions
            max_width_inches = 6.0
            max_width_pixels = int(max_width_inches * 96)
            
            original_size = image.size
            if image.width > max_width_pixels:
                ratio = max_width_pixels / image.width
                new_width = max_width_pixels
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"[DEBUG] Resized image from {original_size} to {image.size}")
            
            # Convert to PNG for consistency
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True)
            img_byte_arr = img_byte_arr.getvalue()
            print(f"[DEBUG] Converted image to PNG format, size: {len(img_byte_arr)} bytes")
            
            # Enhanced placeholder replacement
            found_placeholder = False
            placeholder_count = 0
            
            def process_paragraph(paragraph):
                nonlocal found_placeholder, placeholder_count
                if placeholder in paragraph.text:
                    placeholder_count += 1
                    print(f"[DEBUG] Found placeholder '{placeholder}' in paragraph #{placeholder_count}")
                    
                    # Clear paragraph and add centered image
                    paragraph.clear()
                    run = paragraph.add_run()
                    
                    # Calculate optimal image width
                    width_inches = min(image.width / 96, max_width_inches)
                    
                    # Add image with enhanced formatting
                    run.add_picture(io.BytesIO(img_byte_arr), width=Inches(width_inches))
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                    # Add spacing after image
                    paragraph.space_after = Pt(12)
                    
                    found_placeholder = True
                    print(f"[DEBUG] Successfully embedded image in paragraph #{placeholder_count}")
            
            # Process all document sections
            for paragraph in doc.paragraphs:
                process_paragraph(paragraph)
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            process_paragraph(paragraph)
            
            # Process headers and footers
            for section in doc.sections:
                for paragraph in section.header.paragraphs:
                    process_paragraph(paragraph)
                for paragraph in section.footer.paragraphs:
                    process_paragraph(paragraph)
            
            if not found_placeholder:
                print(f"[WARNING] Placeholder '{placeholder}' not found in document")
                return False
            
            print(f"[DEBUG] Enhanced image embedding completed successfully. Found {placeholder_count} placeholder(s)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Critical error in enhanced image embedding: {str(e)}")
            import traceback
            traceback.print_exc()
            return False 