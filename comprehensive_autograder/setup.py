#!/usr/bin/env python3
"""
Setup script for comprehensive autograder
Creates additional test input files and validates structure
"""

import os
import json
from pathlib import Path

def create_additional_test_files():
    """Create additional test input files for comprehensive coverage"""
    
    # Create additional input files for better coverage
    test_files = {
        'inputs/A_json_processing/malformed.json': '{"key": "[Name]", "value": "Test"',  # Invalid JSON
        'inputs/A_json_processing/valid_complex.json': [
            {"key": "[Grantor Type]", "value": "Entity"},
            {"key": "[Entity Name]", "value": "ABC Corporation"},
            {"key": "[State]", "value": "Delaware"},
            {"key": "[County]", "value": "New Castle"},
            {"key": "[Authorized Signatory]", "value": "John Smith"},
            {"key": "[Title]", "value": "President"}
        ],
        'inputs/B_placeholder_replacement/nested_placeholders.json': [
            {"key": "[Grantor Name 1]", "value": "John"},
            {"key": "[Grantor Name 2]", "value": "Jane"},
            {"key": "[Grantor Name]", "value": "John and Jane Smith"},
            {"key": "[Owner Type]", "value": "married couple"}
        ],
        'inputs/C_signature_blocks/individual_single.json': [
            {"key": "[Grantor Name]", "value": "John Doe"},
            {"key": "[Owner Type]", "value": "individual"},
            {"key": "[Number of Grantor Signatures]", "value": "1"}
        ],
        'inputs/C_signature_blocks/entity_corporation.json': [
            {"key": "[Grantor Name]", "value": "ABC Corporation"},
            {"key": "[Entity Name]", "value": "ABC Corporation"},
            {"key": "[Owner Type]", "value": "corporation"},
            {"key": "[Authorized Signatory]", "value": "John Smith"},
            {"key": "[Title]", "value": "President"}
        ],
        'inputs/C_signature_blocks/entity_trust.json': [
            {"key": "[Grantor Name]", "value": "Smith Family Trust"},
            {"key": "[Entity Name]", "value": "Smith Family Trust"},
            {"key": "[Owner Type]", "value": "trust"},
            {"key": "[Trustee Name]", "value": "Jane Smith"},
            {"key": "[Title]", "value": "Trustee"}
        ],
        'inputs/D_notary_blocks/complex_notary.json': [
            {"key": "[State]", "value": "Texas"},
            {"key": "[County]", "value": "Harris"},
            {"key": "[NAME(S) OF INDIVIDUAL(S)]", "value": "Jane Smith"},
            {"key": "[TYPE OF AUTHORITY]", "value": "President"},
            {"key": "[NAME OF ENTITY OR TRUST WHOM INSTRUMENT WAS EXECUTED FOR]", "value": "ABC Corporation"}
        ],
        'inputs/E_exhibit_generation/multi_parcel.json': [
            {"key": "[APN 1]", "value": "123-456-001"},
            {"key": "[APN 2]", "value": "123-456-002"},
            {"key": "[APN 3]", "value": "123-456-003"},
            {"key": "[Total Acres]", "value": "25.7"},
            {"key": "# of Parcels", "value": "3"}
        ],
        'inputs/E_exhibit_generation/portion_parcels.json': [
            {"key": "[Portion 1]", "value": "North portion"},
            {"key": "[Portion 2]", "value": "South portion"},
            {"key": "[Total Acres]", "value": "15.2"},
            {"key": "# of Parcels", "value": "2"}
        ],
        'inputs/F_image_processing/with_images.json': [
            {"key": "[Image Placeholder]", "value": "[Image]"},
            {"key": "[Watermark Text]", "value": "CONFIDENTIAL"},
            {"key": "[Image Format]", "value": "PNG"}
        ],
        'inputs/F_image_processing/watermark_test.json': [
            {"key": "[Watermark Text]", "value": "DRAFT COPY"},
            {"key": "[Watermark Position]", "value": "center"},
            {"key": "[Watermark Opacity]", "value": "50%"}
        ],
        'inputs/H_error_handling/invalid_data.json': [
            {"key": "[Number of Signatures]", "value": "not_a_number"},
            {"key": "[Date]", "value": "invalid_date_format"},
            {"key": "[Boolean Field]", "value": "maybe"}
        ]
    }
    
    # Create files
    for file_path, content in test_files.items():
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, str):
            # Raw string (e.g., malformed JSON)
            with open(full_path, 'w') as f:
                f.write(content)
        else:
            # JSON content
            with open(full_path, 'w') as f:
                json.dump(content, f, indent=2)
        
        print(f"✅ Created: {file_path}")

def validate_structure():
    """Validate the autograder directory structure"""
    required_dirs = [
        'inputs/A_json_processing',
        'inputs/B_placeholder_replacement', 
        'inputs/C_signature_blocks',
        'inputs/D_notary_blocks',
        'inputs/E_exhibit_generation',
        'inputs/F_image_processing',
        'inputs/G_integration',
        'inputs/H_error_handling',
        'outputs/expected_signatures',
        'outputs/expected_notary',
        'outputs/expected_exhibits',
        'outputs/expected_documents',
        'test_documents'
    ]
    
    required_files = [
        'autograder.py',
        'validators.py',
        'run_all_tests.py',
        'README.md'
    ]
    
    print("🔍 Validating directory structure...")
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_dirs:
        print("❌ Missing directories:")
        for d in missing_dirs:
            print(f"   - {d}")
    
    if missing_files:
        print("❌ Missing files:")
        for f in missing_files:
            print(f"   - {f}")
    
    if not missing_dirs and not missing_files:
        print("✅ All required directories and files present!")
        return True
    
    return False

def main():
    """Main setup function"""
    print("🚀 Setting up Comprehensive Autograder...")
    print("=" * 50)
    
    # Validate current structure
    if validate_structure():
        print("\n📁 Directory structure validated!")
    else:
        print("\n⚠️  Some structure issues found.")
    
    print("\n📝 Creating additional test files...")
    create_additional_test_files()
    
    print("\n✅ Setup complete!")
    print("\n🧪 Ready to run autograder:")
    print("   python autograder.py")
    print("   python run_all_tests.py")

if __name__ == "__main__":
    main()