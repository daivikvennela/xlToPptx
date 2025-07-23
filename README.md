# AI powered Lease Population and Slide Deck Automation

A simple web application that converts Excel files to PowerPoint presentations. The application creates a PowerPoint presentation with a title slide and a data table containing the Excel data.

## Features

- Upload Excel (.xlsx) files
- Automatic conversion to PowerPoint
- Clean and modern web interface
- Maximum file size: 16MB

## Setup

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Click the "Choose File" button to select an Excel file
2. Click "Convert to PowerPoint" to process the file
3. The PowerPoint file will be automatically downloaded

## Requirements

- Python 3.7 or higher
- Flask
- pandas
- openpyxl
- python-pptx

## Notes

- The application creates an 'uploads' directory to temporarily store files
- Excel files are automatically deleted after conversion
- The PowerPoint presentation includes a title slide and a data table 

## Slide Structure & Mapping

This project uses PowerPoint template slides for each section. The mapping between UI sections and template slides is as follows:

| Slide Section                | Slide ID                        | Template File Path                                                    | Slide Index |
|------------------------------|----------------------------------|-----------------------------------------------------------------------|-------------|
| Title                        | title-1                          | templates/slide_templates/msa_exec/Title/msa[title].pptx              | 0           |
| Executive Summary            | exec-summary-1                   | templates/slide_templates/msa_exec/Executive_Summary/ExecSummary.pptx | 0           |
| Module Procurement: Strategy | module-procurement-strategy      | templates/slide_templates/msa_exec/Module_procurement/mp.pptx         | 0           |
| Module Procurement: Supplier | module-procurement-supplier      | templates/slide_templates/msa_exec/Module_procurement/mp.pptx         | 1           |
| Module Procurement: Timeline | module-procurement-timeline      | templates/slide_templates/msa_exec/Module_procurement/mp.pptx         | 2           |
| Module Procurement: Cost     | module-procurement-cost          | templates/slide_templates/msa_exec/Module_procurement/mp.pptx         | 3           |

- Each slide section in the UI is mapped to a specific slide in a template .pptx file.
- The slide editor dynamically generates editable fields for each text box found in the template slide.
- When generating a presentation, only the text boxes present in the template are editable and updated.
- Any extra text boxes are removed, and missing ones are added in the correct position.

This structure makes it easy to add new slides or update existing ones by simply updating the mapping and template files. 

## Template Version 2: Dynamic PPTX Slide Customization

This feature introduces a new tab in the web app for pixel-perfect editing of single-slide PPTX templates. Users can:
- Clone any single-slide template from `templates/slide_templates/msa_exec/mainTemp/`
- Edit only the textboxes (all design elements are 100% preserved)
- Download a new PPTX with only the specified text changed

### Folder Structure
- All templates: `templates/slide_templates/msa_exec/mainTemp/`
- Each `.pptx` has a corresponding `.map.json` with shape/textbox metadata

### Backend Modules
- `slide_utils/shape_mapper.py`: Generates `.map.json` for each template
- `slide_utils/format_preserver.py`: Injects new text into a template, preserving all formatting
- Flask API endpoints:
  - `GET /api/template/{template}`: Returns mapping JSON
  - `POST /api/render_slide`: Returns a new PPTX with updated text

### Frontend
- New tab: 'Template Version 2' (purple color scheme)
- Loads mapping, renders editable textboxes, and allows download of the customized PPTX

### Strict Preservation Rules
- Never modify slide masters, themes, backgrounds, media, images, animations, or any XML beyond `shape.text`
- Only target shapes by `shape_id`
- Only clear text via existing `run.text` objects and set new content on the first run—never create new runs or change formatting
- All PPTX templates are immutable; each request clones directly from them
- Regenerate `.map.json` whenever a designer edits any template PPTX
