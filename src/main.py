from agents import Agent, Runner
from src.models.model import PatientQuery, MedicalContext, QueryClassification
from src.agents import (
    translator_agent,
    general_doctor_agent,
    diagnoser_agent,
    ai_agent,
    native_language_agent,
)

import uuid

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())

def fetch_patient_history(patient_id: str) -> dict:
    """
    Fetch patient medical history from database.
    
    This is a placeholder implementation that returns empty history.
    In production, this should query your actual patient database/EHR system.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary containing patient medical history including:
        - allergies: List of known allergies
        - medications: Current medications
        - conditions: Existing medical conditions
        - past_visits: Previous consultation history
    """
    # Placeholder: Return empty history structure
    # Replace with actual database query in production
    return {
        "allergies": [],
        "medications": [],
        "conditions": [],
        "past_visits": []
    }

async def process_patient_query(query: PatientQuery):
    """Main workflow orchestration"""
    
    # Initialize context
    context = MedicalContext(
        original_language=query.language,
        patient_id=query.patient_id,
        session_id=generate_session_id(),
        medical_history=fetch_patient_history(query.patient_id)
    )
    
    # Phase 1: Translation
    translated = await Runner.run(
        translator_agent,
        query.text,
        context=context
    )
    
    # Phase 2: Triage and Processing
    classification_result = await Runner.run(
        general_doctor_agent,
        translated.final_output,
        context=context
    )
    
    # Debug: Print what we got
    print(f"Classification result type: {type(classification_result.final_output)}")
    print(f"Classification result value: {classification_result.final_output}")
    
    # Extract the QueryClassification object
    # If output_type is set, final_output should already be the typed object
    classification = classification_result.final_output
    if isinstance(classification, str):
        # If it's still a string, something went wrong - try parsing
        print("WARNING: Classification returned as string, attempting to parse")
        import json
        classification_dict = json.loads(classification)
        classification = QueryClassification(**classification_dict)
    
    # Route based on classification
    if classification.is_complex:
        diagnosis = await Runner.run(
            diagnoser_agent,
            translated.final_output,
            context=context
        )
        response = diagnosis.final_output
    else:
        simple_response = await Runner.run(
            ai_agent,
            translated.final_output,
            context=context
        )
        response = simple_response.final_output
    
    # Phase 3: Native Language Translation
    final_response = await Runner.run(
        native_language_agent,
        f"Translate to {query.language}: {response}",
        context=context
    )
    
    return {
        "response": final_response.final_output,
        "classification": classification,
        "session_id": context.session_id
    }