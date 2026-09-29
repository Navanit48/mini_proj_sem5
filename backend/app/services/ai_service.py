"""
AidFlow AI - AI Service
Prompt management and integration with Groq.
"""

from app.utils.groq_client import call_groq
import json

def extract_fields_from_ocr(raw_text: str, document_category: str) -> dict:
    """Extract structured fields from raw OCR text using AI."""
    
    system_prompt = f"""
    You are an expert data extraction AI for Indian government documents.
    Extract the relevant fields from the OCR text provided.
    Document type: {document_category}
    
    Output strictly in JSON format.
    If a field is not found, set its value to null.
    
    Example schema for Aadhaar:
    {{
        "name": "string",
        "dob": "YYYY-MM-DD",
        "gender": "Male/Female/Other",
        "aadhaar_number": "12 digit string without spaces",
        "address": "string"
    }}
    """
    
    user_prompt = f"Extract information from this OCR text:\n\n{raw_text}"
    
    result = call_groq(system_prompt, user_prompt, temperature=0.1)
    return result


def generate_checklist(scheme_name: str, eligibility_summary: str) -> list[dict]:
    """Generate a step-by-step checklist for a scheme application."""
    
    system_prompt = """
    You are an expert government scheme advisor. 
    Based on the scheme details, generate a step-by-step checklist for a citizen applying for it.
    
    Output MUST be a JSON array of objects.
    Each object must have:
    - "title": A short, clear action item (max 10 words)
    - "description": A slightly longer explanation (optional, max 20 words)
    - "due_date_offset_days": Estimated number of days from today this should be done (integer)
    
    Example:
    [
        {
            "title": "Gather required documents",
            "description": "Collect Aadhaar card and income certificate",
            "due_date_offset_days": 2
        }
    ]
    """
    
    user_prompt = f"Scheme: {scheme_name}\nEligibility & Requirements: {eligibility_summary}"
    
    result = call_groq(system_prompt, user_prompt, temperature=0.3, max_tokens=1024)
    
    # If groq wrapper returns a dict with the array inside it, extract it
    if isinstance(result, dict) and len(result.keys()) == 1:
        key = list(result.keys())[0]
        if isinstance(result[key], list):
            return result[key]
            
    if isinstance(result, list):
        return result
        
    # Fallback empty list if parsing failed completely
    return []
