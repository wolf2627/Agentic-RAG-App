from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class MedicalContext(BaseModel):
    """Context passed through the agent workflow"""
    original_language: str
    patient_id: str
    session_id: str
    medical_history: Dict

class PatientQuery(BaseModel):
    text: str
    patient_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

class TranslatedQuery(BaseModel):
    detected_language: str  # Full language name
    language_code: str  # ISO 639-1 code
    translated_text: str
    confidence: float  # 0.0 to 1.0

class QueryClassification(BaseModel):
    is_complex: bool
    is_administrative: bool  # Non-medical queries (appointments, billing, etc.)
    is_safety_critical: bool  # Medication safety, allergies, drug interactions
    category: str  # e.g., "respiratory", "cardiovascular", "administrative", "safety"
    urgency_level: str  # "low", "medium", "high", "emergency"
    reasoning: str
    requires_rag: bool

class DiagnosisResult(BaseModel):
    primary_assessment: str
    differential_diagnoses: List[str]
    confidence_level: float
    supporting_evidence: List[str]
    recommendations: List[str]
    follow_up_needed: bool
    sources: List[str]

class FinalResponse(BaseModel):
    response_text: str
    language: str
    classification: QueryClassification
    diagnosis: Optional[DiagnosisResult]
    session_id: str
    timestamp: datetime