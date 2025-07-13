# Modification Guidelines for Enhancing xAI Service to Extract Replacement Products/Solutions

These guidelines are intended for an AI cursor coder tasked with modifying the `xai_service.py` script to enhance its functionality. The script should not only extract product ranges from Schneider Electric obsolescence letters but also identify replacement products or solutions (e.g., EcoFit solutions) when explicitly mentioned in the source document. The source document may contain multiple retired products with their corresponding modernization products or solutions. The modifications must maintain the script's existing structure, accuracy, and debug capabilities while adding support for extracting replacement information.

## Objectives
1. **Extract Replacement Information**: Modify the script to identify and extract replacement products or solutions (e.g., EcoFit) for retired products when explicitly stated in the source document.
2. **Handle Multiple Products**: Ensure the script can process documents listing multiple retired products and their associated replacements.
3. **Maintain Accuracy**: Adhere to the existing 95%+ accuracy requirement by only extracting explicitly mentioned replacement information, avoiding inference or hallucination.
4. **Preserve Existing Functionality**: Ensure all existing functionality (e.g., product range extraction, debug output, error handling) remains intact.
5. **Structured Output**: Include replacement information in the JSON schema and output it in the `Letter` object.

## Modification Steps

### 1. Update the JSON Schema
Modify the `_build_structured_schema` method to include a new section for replacement products/solutions within the `product_identification` object. This section should capture replacement product details, including names, codes, or EcoFit solutions.

**Action**:
- Add a `replacements` object to the `product_identification` schema with properties for replacement product names, codes, and descriptions.
- Ensure the schema supports multiple replacements per retired product where applicable.
- Update the `required` fields to include `replacements`.

**Example Schema Addition**:
```python
"replacements": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "retired_product": {
                "type": "string",
                "description": "The retired product range or code"
            },
            "replacement_product": {
                "type": "string",
                "description": "Name or range of the replacement product or solution (e.g., EcoFit)"
            },
            "replacement_code": {
                "type": ["string", "null"],
                "description": "Specific replacement product code, if provided"
            },
            "replacement_description": {
                "type": ["string", "null"],
                "description": "Description of the replacement product or solution"
            }
        },
        "required": ["retired_product", "replacement_product"]
    },
    "description": "List of retired products and their corresponding replacements"
}
```

### 2. Modify the Prompt for Extraction
Update the `_build_enhanced_extraction_prompt` method to include instructions for extracting replacement product information. The prompt should explicitly request identification of replacement products or solutions (e.g., EcoFit) and their association with retired products.

**Action**:
- Add a section to the prompt instructing the AI to identify replacement products or solutions (e.g., EcoFit) explicitly mentioned in the text.
- Emphasize that replacement information must be directly stated, not inferred.
- Include guidance to map replacements to specific retired products or ranges.

**Example Prompt Addition**:
```python
"""
- Replacements: Extract any explicitly mentioned replacement products or solutions (e.g., EcoFit) for retired products. Map each replacement to its corresponding retired product range or code. Include replacement product names, codes, and descriptions if available.
- For each retired product, create a replacement entry with:
  - retired_product: The specific product range or code being replaced
  - replacement_product: The name or range of the replacement (e.g., EcoFit solution)
  - replacement_code: The specific replacement product code, if mentioned
  - replacement_description: Any additional details about the replacement
- If no replacements are mentioned, return an empty array for replacements
"""
```

### 3. Update the `extract_comprehensive_metadata` Method
Modify the `extract_comprehensive_metadata` method to handle the extraction of replacement information and incorporate it into the response.

**Action**:
- Ensure the method processes the updated schema with the `replacements` field.
- Validate replacement information in the `_validate_and_enhance_response` method to confirm that replacements are explicitly mentioned in the text.

### 4. Update the `Letter` Object
Modify the `extract_ranges_from_text` method to include replacement information in the `Letter` object.

**Action**:
- Extend the `Letter` class (assumed to be defined in `../models/letter.py`) to include a `replacements` field, which can store a list of replacement mappings.
- Update the method to extract the `replacements` array from the `product_identification` section of the comprehensive metadata and include it in the `Letter` object.

**Example**:
```python
letter = Letter(
    letter_id=document_name,
    ranges=comprehensive_metadata.get("product_identification", {}).get("ranges", []),
    replacements=comprehensive_metadata.get("product_identification", {}).get("replacements", []),
    metadata=LetterMetadata(
        confidence_score=comprehensive_metadata.get("extraction_metadata", {}).get("confidence", 0.0),
        processing_time=processing_time,
        api_model=self.model,
        extraction_method="xai_grok3_enhanced",
        **comprehensive_metadata.get("extraction_metadata", {})
    )
)
```

### 5. Enhance Validation
Update the `_validate_and_enhance_response` method to validate replacement information.

**Action**:
- Add validation logic to the `_validate_and_enhance_response` method to check that replacement products are explicitly mentioned in the text.
- Implement a new method, `_validate_replacements`, to confirm that each replacement entry corresponds to a retired product mentioned in the text.

**Example**:
```python
def _validate_replacements(self, replacements: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Validate extracted replacements against document text.
    
    Args:
        replacements: List of replacement entries.
        text: Document text.
        
    Returns:
        Validated replacements.
    """
    validated_replacements = []
    text_upper = text.upper()
    
    for replacement in replacements:
        retired_product = replacement.get("retired_product", "").upper()
        replacement_product = replacement.get("replacement_product", "").upper()
        
        # Check if both retired and replacement products are mentioned
        if retired_product in text_upper and replacement_product in text_upper:
            validated_replacements.append(replacement)
        else:
            logger.warning(
                f"Replacement entry skipped: retired_product '{retired_product}' "
                f"or replacement_product '{replacement_product}' not found in text"
            )
    
    return validated_replacements
```

### 6. Update Debug Output
Modify the `_write_debug_output` method to include replacement information in the debug output.

**Action**:
- Update the debug data to include the `replacements` field from the `product_identification` section.
- Add a debug console output line to show the number of replacements found.

**Example**:
```python
print(f"🔄 Replacements Found: {len(response.get('product_identification', {}).get('replacements', []))}")
```

### 7. Update the `validate_ranges` Method
Extend the `validate_ranges` method to optionally validate replacement products against known patterns, similar to how ranges are validated.

**Action**:
- Add logic to validate `replacement_product` and `replacement_code` fields against known Schneider Electric product patterns.
- Include validation results in the `validation_results` dictionary.

**Example**:
```python
def validate_ranges(self, ranges: List[str], replacements: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate extracted ranges and replacements against known patterns.
    
    Args:
        ranges: List of extracted ranges.
        replacements: List of replacement entries (optional).
        
    Returns:
        Validation results.
    """
    validation_results = {
        "total_ranges": len(ranges),
        "valid_ranges": [],
        "suspicious_ranges": [],
        "total_replacements": len(replacements) if replacements else 0,
        "valid_replacements": [],
        "suspicious_replacements": [],
        "validation_notes": []
    }
    
    # Validate ranges (existing logic)
    known_patterns = [
        r"^[A-Z]{2,6}(-[A-Z0-9]+)*$",
        r"^[A-Z]+\d+[A-Z]*$",
        r"^[A-Z]+\s+[A-Z0-9]+$",
    ]
    
    for range_name in ranges:
        is_valid = any(re.match(pattern, range_name) for pattern in known_patterns)
        if is_valid:
            validation_results["valid_ranges"].append(range_name)
        else:
            validation_results["suspicious_ranges"].append(range_name)
            validation_results["validation_notes"].append(
                f"Range '{range_name}' doesn't match known patterns"
            )
    
    # Validate replacements
    if replacements:
        for replacement in replacements:
            replacement_product = replacement.get("replacement_product", "")
            replacement_code = replacement.get("replacement_code", "")
            
            is_valid = any(re.match(pattern, replacement_product) for pattern in known_patterns) if replacement_product else False
            if replacement_code:
                is_valid = is_valid and any(re.match(pattern, replacement_code) for pattern in known_patterns)
            
            if is_valid:
                validation_results["valid_replacements"].append(replacement)
            else:
                validation_results["suspicious_replacements"].append(replacement)
                validation_results["validation_notes"].append(
                    f"Replacement '{replacement_product}' or code '{replacement_code}' doesn't match known patterns"
                )
    
    return validation_results
```

### 8. Update Error Handling
Ensure the `_create_error_response` method includes an empty `replacements` array in the `product_identification` section of the error response.

**Example**:
```python
"product_identification": {
    "ranges": [],
    "product_codes": [],
    "product_types": [],
    "descriptions": [],
    "replacements": []
}
```

### 9. Testing Recommendations
- **Test with Sample Documents**: Use sample obsolescence letters containing multiple retired products and their replacements (e.g., EcoFit solutions) to verify extraction accuracy.
- **Validate Output**: Ensure the `Letter` object includes both ranges and replacements, and that replacements are correctly mapped to retired products.
- **Check Debug Output**: Verify that debug files and console output include replacement information.
- **Test Error Cases**: Test with documents lacking replacement information to ensure empty arrays are returned.
- **Validate Patterns**: Confirm that replacement products/codes match Schneider Electric naming conventions.

## Additional Notes
- **API Key Security**: Ensure the API key remains secure and is not exposed in debug outputs.
- **Performance**: Monitor the impact of additional extraction on processing time and adjust `max_tokens` or `timeout` if necessary.
- **Schema Version**: Update the `schema_version` in the `extraction_metadata` to reflect changes (e.g., `v2.1`).
- **Documentation**: Update the docstrings for modified methods to reflect the new functionality.
- **External Dependencies**: No additional dependencies are required, as the existing `requests`, `json`, and `re` modules suffice.

## Example Usage
After modifications, the script should process a document like:
```
"TeSys D contactors (D40-D80) are obsolete as of 2023. Replace with TeSys Deca (D40A-D80A). EcoFit solutions are available."
```
And produce a `Letter` object with:
- `ranges`: ["TeSys D"]
- `replacements`: [{"retired_product": "TeSys D", "replacement_product": "TeSys Deca", "replacement_code": "D40A-D80A", "replacement_description": "EcoFit solutions available"}]