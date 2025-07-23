from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

def extract_paragraph_formatting(paragraph):
    info = {
        'text': paragraph.text,
        'alignment': str(paragraph.alignment),
        'runs': []
    }
    for run in paragraph.runs:
        run_info = {
            'text': run.text,
            'font_name': run.font.name,
            'font_size': run.font.size.pt if run.font.size else None,
            'bold': run.bold,
            'italic': run.italic,
            'underline': run.underline,
            'color': str(run.font.color.rgb) if run.font.color and run.font.color.rgb else None
        }
        info['runs'].append(run_info)
    return info

def extract_block_formatting(docx_path):
    doc = Document(docx_path)
    blocks = []
    for i, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip():
            blocks.append(extract_paragraph_formatting(paragraph))
    return blocks

def print_block_summary(blocks, label):
    print(f"\n=== {label} ===")
    for i, block in enumerate(blocks):
        print(f"Block {i+1}:")
        print(f"  Text: {block['text']}")
        print(f"  Alignment: {block['alignment']}")
        for j, run in enumerate(block['runs']):
            print(f"    Run {j+1}: '{run['text']}' | Font: {run['font_name']} | Size: {run['font_size']} | Bold: {run['bold']} | Italic: {run['italic']} | Underline: {run['underline']} | Color: {run['color']}")

if __name__ == '__main__':
    # Note: first page = signature block, second page = notary block
    print('Extracting from individual[sig:notary].docx...')
    ind_blocks = extract_block_formatting('individual[sig:notary].docx')
    print_block_summary(ind_blocks, 'Individual (Signature/Notary)')
    print('Extracting from entity[signature:notary].docx...')
    ent_blocks = extract_block_formatting('entity[signature:notary].docx')
    print_block_summary(ent_blocks, 'Entity (Signature/Notary)') 