"""
AidFlow AI - Checklist Service
Bridge between Checklist router and AI generation.
"""

from app.services.ai_service import generate_checklist

async def generate_checklist_items(scheme_data: dict) -> list[dict]:
    """
    Generate checklist items for a specific scheme.
    Uses the AI service to parse scheme details and output actionable steps.
    """
    name = scheme_data.get("name", "Unknown Scheme")
    
    # Combine benefits and eligibility for better AI context
    summary = f"""
    Benefits: {scheme_data.get('benefits_summary', '')}
    Eligibility: {scheme_data.get('eligibility_summary', '')}
    Category: {scheme_data.get('category', '')}
    """
    
    items = generate_checklist(name, summary)
    
    # Provide a fallback if AI fails
    if not items:
        return [
            {
                "title": "Review scheme requirements",
                "description": "Read through the official guidelines to ensure you qualify.",
                "due_date_offset_days": 1
            },
            {
                "title": "Gather necessary documents",
                "description": "Collect ID proof, address proof, and any income certificates required.",
                "due_date_offset_days": 3
            },
            {
                "title": "Submit application",
                "description": f"Apply via the official portal: {scheme_data.get('application_url', 'Govt Portal')}",
                "due_date_offset_days": 7
            }
        ]
        
    return items
