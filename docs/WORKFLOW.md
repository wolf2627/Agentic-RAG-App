# Medical AI Assistant - Workflow

This document describes the complete workflow of how a patient query flows through the system, from input to final response.

## Overview

The system processes queries through a **6-stage pipeline** with specialized AI agents at each stage:

1. **Language Detection & Translation**
2. **Patient Context Loading**
3. **Query Classification & Triage**
4. **Specialist Agent Processing**
5. **Response Translation**
6. **Response Delivery**

---

## Stage 1: Language Detection & Translation

### Agent: Language Interpreter
**Model:** `TRANSLATOR_MODEL` (gpt-4.1-nano)

### Process

```
Patient Input (Any Language)
    │
    ├─ Example: "எனக்கு தலைவலி இருக்கு" (Tamil)
    │
    ▼
Language Interpreter Agent
    │
    ├─ Detects language: "Tamil"
    ├─ Language code: "ta"
    ├─ Translates to: "I have a headache"
    ├─ Confidence: 0.95
    │
    ▼
TranslatedQuery Output
```

### Output Structure
```python
{
    "detected_language": "Tamil",
    "language_code": "ta",
    "translated_text": "I have a headache",
    "confidence": 0.95
}
```

### Supported Languages
- English, Spanish, French, German, Italian
- Hindi, Tamil, Telugu, Kannada, Malayalam
- Chinese, Japanese, Korean
- Arabic, Portuguese, Russian
- And 50+ more languages

---

## Stage 2: Patient Context Loading

### Process

```
Patient ID Extraction
    │
    ├─ From: Telegram user_id, phone number, or API patient_id
    │
    ▼
Fetch Patient History
    │
    ├─ allergies: []
    ├─ medications: []
    ├─ conditions: []
    ├─ past_visits: []
    │
    ▼
Build Agent Context
```

### Context Structure
```python
agent_context = {
    "patient_id": "patient_001",
    "medical_history": {
        "allergies": ["penicillin"],
        "medications": ["metformin"],
        "conditions": ["type 2 diabetes"],
        "past_visits": [...]
    }
}
```

**Note:** Currently returns empty history structure. In production, this queries your EHR/patient database.

---

## Stage 3: Query Classification & Triage

### Agent: Triage Nurse
**Model:** `TRIAGE_NURSE_MODEL` (gpt-4.1-nano)

### Classification Categories

#### 1. Administrative Queries
**Examples:**
- "What are your clinic hours?"
- "How do I book an appointment?"
- "Do you accept insurance?"

**Classification:**
```python
{
    "is_administrative": True,
    "is_safety_critical": False,
    "is_complex": False,
    "requires_rag": False,
    "category": "administrative",
    "urgency_level": "low",
    "reasoning": "General clinic information query"
}
```
**Routes to:** Medical Assistant (no patient data needed)

#### 2. Safety-Critical Queries
**Examples:**
- "Can I take ibuprofen?"
- "Is this medication safe for me?"
- "I'm allergic to penicillin, what can I take?"

**Classification:**
```python
{
    "is_administrative": False,
    "is_safety_critical": True,
    "is_complex": False,
    "requires_rag": True,
    "category": "medication_safety",
    "urgency_level": "high",
    "reasoning": "Medication query requiring allergy check"
}
```
**Routes to:** Safety Agent (with RAG)

#### 3. Complex Diagnostic Queries
**Examples:**
- "I have fever, cough, and fatigue for 3 days"
- "My diabetes symptoms are getting worse"
- "What could cause these symptoms?"

**Classification:**
```python
{
    "is_administrative": False,
    "is_safety_critical": False,
    "is_complex": True,
    "requires_rag": True,
    "category": "respiratory",
    "urgency_level": "medium",
    "reasoning": "Multiple symptoms requiring diagnosis"
}
```
**Routes to:** Diagnostic Specialist (with RAG)

#### 4. Simple Medical Queries
**Examples:**
- "What is normal blood pressure?"
- "How can I prevent colds?"
- "What are symptoms of flu?"

**Classification:**
```python
{
    "is_administrative": False,
    "is_safety_critical": False,
    "is_complex": False,
    "requires_rag": False,
    "category": "general_health",
    "urgency_level": "low",
    "reasoning": "General health information"
}
```
**Routes to:** Medical Assistant (general guidance)

### Urgency Levels
- **low:** Routine information, no immediate action needed
- **medium:** Should be addressed soon, monitor symptoms
- **high:** Needs attention, potential health risk
- **emergency:** Immediate medical attention required

---

## Stage 4: Specialist Agent Processing

### Route A: Medical Assistant
**Used for:** Administrative + Simple medical queries
**Model:** `MEDICAL_ASSISTANT_MODEL` (gpt-4.1-nano)

```
Query
    │
    ▼
Medical Assistant
    │
    ├─ No RAG access
    ├─ General knowledge only
    ├─ Provides education & guidance
    │
    ▼
Response: General information
```

**Example Response:**
> "Normal blood pressure for adults is typically around 120/80 mmHg. Blood pressure between 120-129 systolic and less than 80 diastolic is considered elevated..."

---

### Route B: Safety Agent
**Used for:** Safety-critical medication queries
**Model:** `SAFETY_AGENT_MODEL` (gpt-4o)

```
Query: "Can I take aspirin?"
    │
    ▼
Safety Agent
    │
    ├─ Calls: check_patient_safety()
    │     │
    │     ├─ Builds RAG query:
    │     │   "For patient_001, retrieve:
    │     │    1. ALL known allergies
    │     │    2. Current medications
    │     │    3. Recent adverse reactions"
    │     │
    │     ├─ Retrieves from Vector Store:
    │     │   • Filter: patient_id=patient_001
    │     │   • Top-k: 5 chunks
    │     │
    │     └─ Returns safety context:
    │         - Allergies: [penicillin, NSAIDs]
    │         - Medications: [metformin]
    │         - Contraindications detected
    │
    ├─ Analyzes safety
    ├─ Checks drug interactions
    ├─ Verifies allergies
    │
    ▼
Safety Assessment Response
```

**Example Response:**
> "⚠️ CAUTION: Your medical records indicate you have an allergy to NSAIDs (Non-Steroidal Anti-Inflammatory Drugs). Aspirin is an NSAID and should NOT be taken.
>
> Alternative options:
> - Acetaminophen (Tylenol) for pain relief
> - Consult your doctor for safe alternatives
>
> Please speak with your healthcare provider before taking any new medication."

---

### Route C: Diagnostic Specialist
**Used for:** Complex diagnostic queries
**Model:** `DIAGNOSER_MODEL` (gpt-4o)

```
Query: "I have fever and cough for 3 days"
    │
    ▼
Diagnostic Specialist
    │
    ├─ Calls: retrieve_medical_knowledge()
    │     │
    │     ├─ Builds RAG query:
    │     │   "Patient symptoms: fever, cough, 3 days
    │     │    Retrieve relevant medical history"
    │     │
    │     ├─ Retrieves from Vector Store:
    │     │   • Filter: patient_id=patient_001
    │     │   • Top-k: 10 chunks
    │     │   • Sources: medical_history.md, visits.md
    │     │
    │     └─ Returns medical context:
    │         - Past respiratory infections
    │         - Known conditions (asthma, diabetes)
    │         - Recent visits
    │         - Current medications
    │
    ├─ Analyzes symptoms
    ├─ Considers patient history
    ├─ Provides differential diagnosis
    ├─ Recommends next steps
    │
    ▼
Diagnostic Assessment Response
```

**Example Response:**
> "Based on your symptoms (fever and cough for 3 days) and your medical history:
>
> **Possible Causes:**
> 1. Upper respiratory infection (most likely)
> 2. Bronchitis
> 3. Given your diabetes, we should monitor more closely
>
> **Recommendations:**
> - Monitor temperature (if >101°F, seek care)
> - Stay hydrated
> - Rest
> - Your diabetes may affect recovery time
>
> **When to Seek Care:**
> - Difficulty breathing
> - Persistent high fever
> - Symptoms worsening after 3 days
>
> **Sources:** Based on your medical record from [medical_history.md]"

---

## Stage 5: Response Translation

### Agent: Response Translator
**Model:** `NATIVE_LANGUAGE_MODEL` (gpt-4.1-nano)

### Process

```
English Response
    │
    ├─ Example: "Based on your symptoms..."
    │
    ▼
Response Translator
    │
    ├─ Target language: Tamil (from Stage 1)
    ├─ Translates medical terms accurately
    ├─ Preserves urgency and tone
    │
    ▼
Native Language Response
    │
    └─ "உங்கள் அறிகுறிகளின் அடிப்படையில்..."
```

### Translation Quality
- Preserves medical terminology
- Maintains urgency level
- Cultural sensitivity
- Accurate dosage/measurement units

---

## Stage 6: Response Delivery

### Final Response Structure

```json
{
    "response": "உங்கள் அறிகுறிகளின் அடிப்படையில்...",
    "detected_language": "Tamil",
    "language_code": "ta",
    "confidence": 0.95,
    "classification": {
        "is_complex": true,
        "is_administrative": false,
        "is_safety_critical": false,
        "category": "respiratory",
        "urgency_level": "medium",
        "reasoning": "Multiple symptoms requiring diagnosis",
        "requires_rag": true
    },
    "session_id": "sess_abc123xyz"
}
```

---

## Complete Example: Complex Query Flow

### Patient Query (Tamil)
```
"எனக்கு ரெண்டு நாளா காய்ச்சலும் இருமலும் இருக்கு. 
நான் சர்க்கரை நோயாளி. என்ன செய்யலாம்?"

Translation: "I have had fever and cough for 2 days. 
I'm a diabetes patient. What should I do?"
```

### Stage-by-Stage Processing

**Stage 1 - Language Detection:**
```python
{
    "detected_language": "Tamil",
    "language_code": "ta",
    "translated_text": "I have had fever and cough for 2 days. I'm a diabetes patient. What should I do?",
    "confidence": 0.98
}
```

**Stage 2 - Context Loading:**
```python
{
    "patient_id": "patient_001",
    "medical_history": {
        "conditions": ["type 2 diabetes"],
        "medications": ["metformin"],
        "allergies": [],
        "past_visits": [...]
    }
}
```

**Stage 3 - Classification:**
```python
{
    "is_complex": true,
    "is_safety_critical": false,
    "is_administrative": false,
    "category": "respiratory",
    "urgency_level": "high",  # High due to diabetes
    "reasoning": "Fever with cough in diabetic patient requires careful assessment",
    "requires_rag": true
}
```
**Routes to:** Diagnostic Specialist

**Stage 4 - Diagnosis:**
```
Diagnostic Specialist:
├─ Calls retrieve_medical_knowledge()
├─ RAG retrieves:
│   • Diabetes management history
│   • Past respiratory infections
│   • Current medication list
├─ Analyzes with patient context
└─ Generates comprehensive response
```

**Stage 5 - Translation:**
```
Translates response back to Tamil with:
├─ Medical accuracy preserved
├─ Urgency conveyed
└─ Culturally appropriate phrasing
```

**Stage 6 - Delivery:**
```
Complete response delivered via:
├─ Telegram bot
├─ API endpoint
└─ Or other integrated platform
```

---

## RAG Integration Details

### When RAG is Used
- ✅ Safety-critical queries (medications, allergies)
- ✅ Complex diagnostic queries
- ❌ Administrative queries
- ❌ Simple general health questions

### RAG Query Process

```
1. Build Context-Aware Query
   │
   ├─ Include patient symptoms
   ├─ Add medical context needed
   └─ Specify retrieval focus
   │
   ▼
2. Vector Search
   │
   ├─ Embed query (text-embedding-3-large)
   ├─ Filter by patient_id
   ├─ Cosine similarity search
   └─ Retrieve top-k chunks (default: 10)
   │
   ▼
3. Format Results
   │
   ├─ Include source attribution
   ├─ Add relevance scores
   └─ Present to agent
   │
   ▼
4. Agent Processing
   │
   ├─ Reads retrieved context
   ├─ Synthesizes with query
   └─ Generates informed response
```

### Privacy & Security
- All RAG queries filtered by `patient_id`
- No cross-patient data access
- Source documents isolated per patient
- Vector store enforces patient boundaries

---

## Error Handling

### Query Processing Errors
```
Error Detected
    │
    ├─ Translation failure → Fallback to English
    ├─ Classification failure → Default to Medical Assistant
    ├─ RAG retrieval failure → Proceed without context + warning
    ├─ Agent processing failure → Generic safe response
    └─ Response translation failure → Return English response
```

### Safety Fallbacks
- Medication queries without safety check → Refuse + recommend doctor
- Uncertain diagnosis → Conservative response + seek professional care
- Emergency indicators → Immediate escalation message

---

## Performance Characteristics

### Latency Breakdown (Typical)
- Language Detection: 300-500ms
- Context Loading: 10-50ms
- Classification: 300-500ms
- RAG Retrieval: 200-800ms (if used)
- Agent Processing: 1-3s
- Response Translation: 300-500ms

**Total:** 2-5 seconds (depending on complexity and RAG usage)

### Optimization Strategies
- Parallel processing where possible
- Caching for frequent queries
- Efficient RAG indexing
- Model selection per task complexity

---

## Key Workflow Principles

1. **Language Inclusivity:** Detect and translate any language automatically
2. **Patient Privacy:** All data access scoped to specific patient
3. **Safety First:** Critical queries mandatory use RAG and safety checks
4. **Intelligent Routing:** Right specialist for each query type
5. **Source Attribution:** All medical guidance cites source documents
6. **Graceful Degradation:** System continues even if components fail
7. **Audit Trail:** All decisions logged for review and improvement
