# Medical AI Assistant - Architecture

## Core Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Client Applications                              │
│              (Telegram, WhatsApp, Web Chat, API)                     │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          Gateway                                     │
│                        (api.py / main.py)                            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Multi-Agent Workflow                           │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐                              │
│  │   Language   │───▶│    Triage     │                              │
│  │  Interpreter │     │    Nurse     │                              │
│  └──────────────┘     └──────┬───────┘                              │
│                              │                                      │
│                              │ Classification Routes:               │
│                              │                                      │
│              ┌───────────────┼───────────────┐                      │
│              │               │               │                      │
│         Administrative   Safety         Complex                     │
│         or Simple       Critical       Diagnostic                   │
│              │               │               │                      │
│              ▼               ▼               ▼                      │
│       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│       │  Medical    │ │   Safety    │ │ Diagnostic  │               │
│       │  Assistant  │ │   Agent     │ │  Specialist │               │
│       │             │ │  (+ RAG)    │ │  (+ RAG)    │               │
│       └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
│              │               │               │                      │
│              └───────────────┼───────────────┘                      │
│                              │                                      │
│                              ▼                                      │
│                   ┌────────────────────┐                            │
│                   │     Response       │                            │
│                   │    Translator      │                            │
│                   └─────────┬──────────┘                            │
│                             │                                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │   Response    │
                      └───────────────┘
```

## Agent System

### 1. Language Interpreter (Translator Agent)
**Model:** Configurable via `TRANSLATOR_MODEL` (default: gpt-4.1-nano)

**Responsibilities:**
- Detects input language automatically
- Translates query to English for processing
- Returns structured output with language metadata

**Output:**
```python
TranslatedQuery:
  - detected_language: str  # Full name (e.g., "Tamil")
  - language_code: str      # ISO code (e.g., "ta")
  - translated_text: str    # English translation
  - confidence: float       # Detection confidence (0-1)
```

### 2. Triage Nurse (Classification Agent)
**Model:** Configurable via `TRIAGE_NURSE_MODEL` (default: gpt-4.1-nano)

**Responsibilities:**
- Classifies queries into categories
- Determines urgency level
- Routes to appropriate specialist agent
- Applies input safety guardrails

**Output:**
```python
QueryClassification:
  - is_administrative: bool      # Appointments, billing
  - is_safety_critical: bool     # Medications, allergies
  - is_complex: bool             # Diagnostic cases
  - requires_rag: bool           # Needs patient data
  - category: str                # Symptom category
  - urgency_level: str           # low/medium/high/emergency
  - reasoning: str               # Classification logic
```

**Routing Logic:**
- **Administrative** → Medical Assistant (no RAG)
- **Safety Critical** → Safety Agent (with RAG - allergies, medications)
- **Complex** → Diagnostic Specialist (with RAG - full medical records)
- **Simple/Other** → Medical Assistant (no RAG)

### 3. Medical Assistant
**Model:** Configurable via `MEDICAL_ASSISTANT_MODEL` (default: gpt-4.1-nano)

**Responsibilities:**
- Handles simple medical queries
- Administrative tasks (appointments, clinic info)
- General health education
- Does not access patient records

**Use Cases:**
- "What are clinic hours?"
- "How can I book an appointment?"
- "What is normal blood pressure?"

### 4. Diagnostic Specialist
**Model:** Configurable via `DIAGNOSER_MODEL` (default: gpt-4o)

**Responsibilities:**
- Complex symptom analysis
- Differential diagnosis
- Chronic condition management
- **Uses RAG** to retrieve patient medical records

**Tools:**
- `retrieve_medical_knowledge()` - Fetches patient-specific data from vector store

**RAG Integration:**
- Searches patient's medical documents
- Retrieves relevant chunks (top-k=10)
- Provides source attribution
- Filters by patient_id

### 5. Safety Agent
**Model:** Configurable via `SAFETY_AGENT_MODEL` (default: gpt-4o)

**Responsibilities:**
- Medication safety checks
- Allergy verification
- Drug interaction analysis
- Contraindication warnings
- **Mandatory RAG usage** for all queries

**Tools:**
- `check_patient_safety()` - Retrieves allergies, medications, adverse reactions

**Critical Safety Rules:**
- NEVER recommend medications the patient is allergic to
- ALWAYS check drug interactions
- ALWAYS err on side of caution
- Recommend professional consultation for uncertain cases

### 6. Response Translator
**Model:** Configurable via `NATIVE_LANGUAGE_MODEL` (default: gpt-4.1-nano)

**Responsibilities:**
- Translates final response to patient's native language
- Preserves medical terminology accuracy
- Maintains tone and urgency level

## RAG (Retrieval-Augmented Generation) System

### Vector Store Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Storage                          │
│              (documents/{patient_id}/*.md)                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Document Ingestion                         │
│  • Load documents (txt, md, pdf, pptx)                       │
│  • Chunk text (50 words, 5-word overlap)                     │
│  • Generate embeddings (text-embedding-3-large)              │
│  • Store in ChromaDB with patient_id metadata                │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     ChromaDB Vector Store                    │
│  • Persistent SQLite backend (embeddings/)                   │
│  • Cosine similarity search                                  │
│  • Patient-specific filtering                                │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Processing                          │
│  • Embed query                                               │
│  • Filter by patient_id                                      │
│  • Retrieve top-k chunks (default: 10)                       │
│  • Return with source attribution                            │
└──────────────────────────────────────────────────────────────┘
```

### RAG Configuration

**Environment Variables:**
- `EMBED_MODEL` - Embedding model (default: text-embedding-3-large)
- `CHUNK_SIZE` - Words per chunk (default: 50)
- `CHUNK_OVERLAP` - Overlap between chunks (default: 5)
- `TOP_K` - Number of chunks to retrieve (default: 10)

**Patient Data Isolation:**
All RAG queries include `patient_id` filter to ensure:
- Patients only access their own medical records
- No cross-patient data leakage
- Privacy compliance

## Data Flow

### Complete Query Processing Flow

```
1. Patient Query (Any Language)
   │
   ▼
2. Language Interpreter
   ├─ Detect language
   ├─ Translate to English
   └─ Return TranslatedQuery
   │
   ▼
3. Fetch Patient Context
   ├─ Get medical history
   └─ Prepare agent context
   │
   ▼
4. Triage Nurse
   ├─ Classify query type
   ├─ Assess urgency
   └─ Determine routing
   │
   ▼
5. Route to Specialist (PARALLEL - ONE route chosen)
   │
   ├─ Administrative?     → Medical Assistant
   │                         (No RAG)
   │                         └─ Returns response
   │
   ├─ Safety Critical?    → Safety Agent
   │                         └─ check_patient_safety() tool
   │                             └─ RAG: allergies, medications
   │                             └─ Returns safety-checked response
   │
   ├─ Complex Diagnosis?  → Diagnostic Specialist
   │                         └─ retrieve_medical_knowledge() tool
   │                             └─ RAG: full patient records
   │                             └─ Returns diagnostic response
   │
   └─ Simple Medical?     → Medical Assistant
                             (General guidance, no RAG)
                             └─ Returns response
   │
   ▼
6. Response Translator
   ├─ Translate to patient's language
   └─ Return final response
   │
   ▼
7. Return to Client
   ├─ response text
   ├─ classification
   ├─ language metadata
   └─ session_id
```

## Configuration System

### Agent Models
All agent models are configurable via environment variables:

```env
# Agent Models
TRIAGE_NURSE_MODEL=gpt-4.1-nano
MEDICAL_ASSISTANT_MODEL=gpt-4.1-nano
DIAGNOSER_MODEL=gpt-4o
SAFETY_AGENT_MODEL=gpt-4o
TRANSLATOR_MODEL=gpt-4.1-nano
NATIVE_LANGUAGE_MODEL=gpt-4.1-nano

# Voice/Audio
WHISPER_MODEL=whisper-1

# Embeddings
EMBED_MODEL=text-embedding-3-large
```

### Model Selection Guidelines

**gpt-4.1-nano:**
- Fast and cost-effective
- Suitable for classification and translation
- Used for: Triage, Translation, Simple queries

**gpt-4o:**
- More capable for complex reasoning
- Better medical knowledge
- Used for: Diagnosis, Safety analysis

## Security & Privacy

### Patient Data Protection
- Patient-specific document folders: `documents/{patient_id}/`
- RAG queries filtered by `patient_id`
- No cross-patient data access
- Vector store metadata includes patient isolation

### Input Safety
- Guardrails on all user inputs
- Emergency query detection
- Prompt injection prevention
- Content filtering

### Medical Safety
- Mandatory safety checks for medication queries
- Allergy verification before recommendations
- Drug interaction warnings
- Conservative approach to uncertain cases

## Scalability Considerations

### Current Architecture
- Single-process FastAPI server
- Embedded ChromaDB (SQLite)
- In-memory agent initialization

### Scaling Strategies

**Horizontal Scaling:**
- Multiple API workers (Gunicorn/Uvicorn)
- Load balancer (nginx)
- Shared ChromaDB server mode

**Vertical Scaling:**
- Larger models for better accuracy
- More CPU/RAM for concurrent requests
- SSD for faster vector search

**Database Scaling:**
- ChromaDB client-server mode
- Managed vector DBs (Pinecone, Weaviate)
- PostgreSQL with pgvector

## Monitoring & Observability

### Key Metrics to Track
- Request latency per agent
- Classification accuracy
- RAG retrieval relevance
- Language detection accuracy
- Safety check effectiveness
- Model costs (tokens consumed)

### Logging
- Agent transitions and handoffs
- RAG retrieval results
- Classification decisions
- Error traces with context

## Future Enhancements

### Planned Features
- [ ] Conversation history with MongoDB
- [ ] Multi-turn conversation support
- [ ] Conversation summarization
- [ ] Voice output support
- [ ] Real-time streaming responses
- [ ] Doctor handoff capability
- [ ] Appointment scheduling integration

### Under Consideration
- [ ] Medical image analysis
- [ ] Lab result interpretation
- [ ] Symptom timeline tracking
- [ ] Treatment plan monitoring
- [ ] Emergency escalation protocols

---

## Key Design Principles

1. **Multi-Agent Specialization:** Each agent has a clear, focused responsibility
2. **Patient Privacy First:** All data access is patient-scoped and filtered
3. **Safety Critical:** Medication queries mandatory use RAG and safety checks
4. **Language Agnostic:** Automatic detection and translation for global access
5. **Configurable Models:** All AI models can be swapped via environment config
6. **RAG-Powered:** Medical guidance grounded in patient's actual records
7. **Traceable Decisions:** All classifications and routing logged for audit
