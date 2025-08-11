"""
Validation utilities for lease population autograder
"""

from typing import List, Tuple, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    details: Any = None

def validate_signature_block(signature_block: str, expected_elements: List[str]) -> ValidationResult:
    """Validate signature block content"""
    if not signature_block or len(signature_block) < 20:
        return ValidationResult(False, "Signature block too short or empty")
    
    missing_elements = []
    for element in expected_elements:
        if element not in signature_block:
            missing_elements.append(element)
    
    if missing_elements:
        return ValidationResult(False, f"Missing elements: {missing_elements}")
    
    return ValidationResult(True, "Signature block validation passed")

def validate_notary_block(notary_block: str, expected_elements: List[str]) -> ValidationResult:
    """Validate notary block content"""
    if not notary_block or len(notary_block) < 50:
        return ValidationResult(False, "Notary block too short or empty")
    
    missing_elements = []
    for element in expected_elements:
        if element not in notary_block:
            missing_elements.append(element)
    
    if missing_elements:
        return ValidationResult(False, f"Missing notary elements: {missing_elements}")
    
    return ValidationResult(True, "Notary block validation passed")

def validate_exhibit_string(exhibit_string: str, expected_parcel_count: int) -> ValidationResult:
    """Validate exhibit string content"""
    if not exhibit_string or len(exhibit_string) < 20:
        return ValidationResult(False, "Exhibit string too short or empty")
    
    if "EXHIBIT A" not in exhibit_string:
        return ValidationResult(False, "Missing 'EXHIBIT A' header")
    
    # Count parcel references (more flexible counting)
    parcel_count = exhibit_string.count("Parcel ") + exhibit_string.count("Portion ")
    if parcel_count < expected_parcel_count:
        return ValidationResult(False, f"Expected {expected_parcel_count} parcels, found {parcel_count}")
    
    return ValidationResult(True, "Exhibit string validation passed")

def validate_json_structure(data: Any) -> ValidationResult:
    """Validate JSON mapping structure"""
    if not isinstance(data, list):
        return ValidationResult(False, "Expected list format for JSON mapping")
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return ValidationResult(False, f"Item {i} is not a dictionary")
        
        if 'key' not in item or 'value' not in item:
            return ValidationResult(False, f"Item {i} missing 'key' or 'value' field")
        
        if not isinstance(item['key'], str) or not isinstance(item['value'], str):
            return ValidationResult(False, f"Item {i} has non-string key or value")
    
    return ValidationResult(True, "JSON structure validation passed")