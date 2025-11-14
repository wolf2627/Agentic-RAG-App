# Documentation Index

Welcome to the Medical AI Assistant documentation. This guide will help you understand and work with the system.

## Core Documentation

### [Architecture](ARCHITECTURE.md)
Complete system architecture including:
- Multi-agent system design
- Agent responsibilities and models
- RAG (Retrieval-Augmented Generation) integration
- Data flow and routing logic
- Security and privacy considerations
- Configuration system
- Scalability and monitoring

**Read this to understand:** How the system is designed and why decisions were made.

### [Workflow](WORKFLOW.md)
Detailed query processing workflow including:
- 6-stage processing pipeline
- Language detection and translation
- Query classification and triage
- Agent routing and specialization
- RAG retrieval process
- Error handling and safety fallbacks
- Performance characteristics

**Read this to understand:** How a patient query flows through the system from input to response.

### [API Reference](api.md)
API endpoints and integration guide:
- Endpoint specifications
- Request/response schemas
- Error handling
- Integration examples

**Read this to:** Integrate the system with your applications.

## Quick Navigation

### Getting Started
1. Read [README.md](../README.md) for installation and quick start
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
3. Study [WORKFLOW.md](WORKFLOW.md) for detailed processing flow
4. Check [api.md](api.md) for API integration

## Key Concepts

### Multi-Agent System
The system uses 6 specialized AI agents, each with a specific role:
1. **Language Interpreter** - Language detection and translation
2. **Triage Nurse** - Query classification and routing
3. **Medical Assistant** - Simple queries and admin tasks
4. **Diagnostic Specialist** - Complex diagnosis with RAG
5. **Safety Agent** - Safety checks with RAG
6. **Response Translator** - Back to native language

### RAG (Retrieval-Augmented Generation)
- Retrieves patient-specific medical records from vector database
- Ensures responses are grounded in actual patient data
- Mandatory for medication safety and diagnostic queries
- All queries filtered by patient_id for privacy

### Query Classification
Queries are classified into 4 types:
- **Administrative**: Clinic info, appointments (→ Medical Assistant)
- **Safety-Critical**: Medications, allergies (→ Safety Specialist + RAG)
- **Complex**: Multi-symptom diagnosis (→ Diagnostic Specialist + RAG)
- **Simple Medical**: General health info (→ Medical Assistant)

### Multi-Language Support
- Automatic detection of languages
- Translation to English for processing
- Response translated back to patient's language
- Medical terminology preserved accurately

## Configuration

### Agent Models
All AI models are configurable via environment variables:

```env
TRIAGE_NURSE_MODEL=gpt-4.1-nano          # Fast classification
MEDICAL_ASSISTANT_MODEL=gpt-4.1-nano     # Simple queries
DIAGNOSER_MODEL=gpt-4o                   # Complex reasoning
SAFETY_AGENT_MODEL=gpt-4o                # Critical safety
TRANSLATOR_MODEL=gpt-4.1-nano            # Language tasks
NATIVE_LANGUAGE_MODEL=gpt-4.1-nano       # Response translation
```

### RAG Configuration
```env
EMBED_MODEL=text-embedding-3-large       # Vector embeddings
CHUNK_SIZE=50                            # Words per chunk
CHUNK_OVERLAP=5                          # Overlap between chunks
TOP_K=10                                 # Chunks to retrieve
```

## Patient Data Structure

```
documents/
  ├── patient_001/
  │   ├── medical_history.md
  │   ├── medications.md
  │   ├── allergies.md
  │   └── lab_results.md
  ├── patient_002/
  │   └── medical_records.md
  └── ...
```

## Safety & Privacy

- ✅ Patient data isolated by patient_id
- ✅ RAG queries filtered per patient
- ✅ Mandatory safety checks for medications
- ✅ Emergency query detection
- ✅ Input validation and guardrails
- ✅ No cross-patient data access

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check this folder for detailed guides
- **Examples**: See WORKFLOW.md for real-world examples

---

**Last Updated**: November 14, 2025
