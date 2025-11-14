from agents import Agent, Runner
from src.models.model import PatientQuery, MedicalContext, QueryClassification, TranslatedQuery
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
    
    # Phase 1: Translation and Language Detection
    translation_result = await Runner.run(
        translator_agent,
        query.text,
        context=None
    )
    
    # Extract the TranslatedQuery object
    translation: TranslatedQuery = translation_result.final_output
    
    print(f"Detected Language: {translation.detected_language} ({translation.language_code})")
    print(f"Confidence: {translation.confidence}")
    print(f"Translation: {translation.translated_text}")
    
    # Initialize context with detected language
    medical_history = fetch_patient_history(query.patient_id)
    context = MedicalContext(
        original_language=translation.language_code,
        patient_id=query.patient_id,
        session_id=generate_session_id(),
        medical_history=medical_history
    )
    
    # Prepare context dict for agents
    agent_context = {
        "patient_id": query.patient_id,
        "medical_history": medical_history
    }
    
    # Phase 2: Triage and Processing
    classification_result = await Runner.run(
        general_doctor_agent,
        translation.translated_text,
        context=agent_context
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
    if classification.is_administrative:
        # Administrative queries (appointments, billing, etc.) - no medical context needed
        administrative = await Runner.run(
            ai_agent,
            translation.translated_text,
            context=agent_context
        )
        response = administrative.final_output
    
    elif classification.is_safety_critical:
        # Safety-critical route (medication safety, allergies, drug interactions)
        from src.agents import safety_agent
        safety = await Runner.run(
            safety_agent,
            translation.translated_text,
            context=agent_context
        )
        response = safety.final_output
    
    elif classification.is_complex:
        # Complex diagnostic route with RAG
        diagnosis = await Runner.run(
            diagnoser_agent,
            translation.translated_text,
            context=agent_context
        )
        response = diagnosis.final_output
    
    else:
        # Simple medical queries
        simple_response = await Runner.run(
            ai_agent,
            translation.translated_text,
            context=agent_context
        )
        response = simple_response.final_output
    
    # Phase 3: Native Language Translation
    final_response = await Runner.run(
        native_language_agent,
        f"Translate to {translation.detected_language}: {response}",
        context=agent_context  # Pass complete context including medical history
    )
    
    return {
        "response": final_response.final_output,
        "detected_language": translation.detected_language,
        "language_code": translation.language_code,
        "confidence": translation.confidence,
        "classification": classification,
        "session_id": context.session_id
    }