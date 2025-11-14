# Medical AI Assistant

A multi-agent conversational AI system that provides intelligent medical guidance through natural language interaction. The system supports multiple languages, uses RAG (Retrieval-Augmented Generation) for patient-specific medical data, and intelligently routes queries through specialized medical AI agents.

## Features

- **Multi-Language Support**: Automatic language detection and translation
- **Multi-Agent System**: Specialized agents for triage, diagnosis, safety, and general medical queries
- **RAG-Powered**: Retrieves patient-specific medical records for informed responses
- **Patient Privacy**: All medical data access is patient-scoped and isolated
- **Medication Safety**: Mandatory allergy and interaction checks for medication queries
- **Intelligent Routing**: Classifies queries and routes to appropriate specialist
- **Platform Agnostic**: Works with Telegram (can be implemented with WhatsApp, Web, or direct API)

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/wolf2627/Agentic-RAG-App.git
cd Agentic-RAG-App

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY and other configurations to .env
```

### Configuration

Edit `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Agent Models (Optional - defaults provided)
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

### Running the System

```bash
# Index patient medical documents (if you have documents in documents/ folder)
make index

# Start the API server
make dev

# Or run Telegram bot
make bot
```

API available at: `http://localhost:8000`

## System Architecture

### Multi-Agent Workflow

```
Patient Query (Any Language)
    ↓
Language Interpreter → Detects & translates language
    ↓
Triage Nurse → Classifies query & determines route
    ↓
    ├─ Administrative or Simple Medical → Medical Assistant
    ├─ Safety-Critical → Medication Safety Specialist (+ RAG)
    └─ Complex Diagnosis → Diagnostic Specialist (+ RAG)
    ↓
Response Translator → Translates back to patient's language
    ↓
Final Response
```

### Specialized Agents

1. **Language Interpreter**: Detects input language, translates to English
2. **Triage Nurse**: Classifies queries, determines urgency, routes to specialist
3. **Medical Assistant**: Handles simple queries and administrative tasks
4. **Diagnostic Specialist**: Complex symptom analysis with patient medical records
5. **Medication Safety Specialist**: Safety checks for medications with allergy verification
6. **Response Translator**: Translates responses back to patient's native language

## Usage Examples

### Via API

```bash
# Simple query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I have a headache",
    "patient_id": "patient_001"
  }'

# Multi-language query (Tamil)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "எனக்கு தலைவலி இருக்கு",
    "patient_id": "patient_001"
  }'
```

### Via Telegram Bot

```python
# Set TELEGRAM_BOT_TOKEN in .env
# Run: make bot

# Users can:
# - Send text messages in any language
# - Send voice messages
# - Get medical guidance
# - Register with patient ID
```

### Response Format

```json
{
  "response": "Based on your symptoms...",
  "detected_language": "Tamil",
  "language_code": "ta",
  "confidence": 0.95,
  "classification": {
    "is_complex": false,
    "is_administrative": false,
    "is_safety_critical": false,
    "category": "general_health",
    "urgency_level": "low",
    "requires_rag": false
  },
  "session_id": "sess_abc123xyz"
}
```

## Patient Medical Documents

Place patient-specific medical documents in:
```
documents/
  ├── patient_001/
  │   ├── medical_history.md
  │   ├── medications.md
  │   └── allergies.md
  ├── patient_002/
  │   └── medical_records.md
  └── ...
```

Supported formats: `.txt`, `.md`, `.pdf`

Run `make index` to index documents into the vector database.

## Platform Integration

### Telegram

```bash
# Set in .env:
TELEGRAM_BOT_TOKEN=your_bot_token

# Run bot:
make bot
```

### WhatsApp (via Twilio)

Integrate via webhook - see Telegram bot implementation as reference.

### Web Chat

Use the `/query` API endpoint with your web frontend.

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design, components, and data flow
- **[Workflow](docs/WORKFLOW.md)** - Complete query processing pipeline with examples
- **[API Reference](docs/api.md)** - API endpoints and schemas

## Development

### Commands

```bash
make dev      # Run development server with hot reload
make bot      # Run Telegram bot
make index    # Index documents into vector database
make clean    # Clean cache files
make help     # Show all commands
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Project Structure

```
.
├── api.py                 # FastAPI application entry point
├── src/
│   ├── main.py           # Main orchestration workflow
│   ├── agents/           # Specialized AI agents
│   │   ├── triage_nurse.py
│   │   ├── medical_assistant.py
│   │   ├── diagnoser.py
│   │   ├── safety_agent.py
│   │   ├── translator.py
│   │   └── native_language.py
│   ├── models/           # Data models
│   ├── rag/              # RAG system
│   │   ├── vector_store.py
│   │   ├── openai_client.py
│   │   └── ingest.py
│   └── guardrails/       # Input validation
├── documents/            # Patient medical documents
├── embeddings/           # Vector database
├── telegram_bot.py       # Telegram bot integration
└── docs/                 # Documentation
```

## Technology Stack

- **OpenAI Agents SDK** - Multi-agent orchestration
- **FastAPI** - Modern async web framework
- **ChromaDB** - Vector database for embeddings
- **OpenAI API** - LLMs and embeddings
- **Pydantic** - Data validation
- **Telegram Bot API** - Messaging platform integration

## Security & Privacy

- Patient data isolated by `patient_id`
- RAG queries filtered to prevent cross-patient data access
- Input safety guardrails
- Medication safety checks mandatory for relevant queries
- Environment-based configuration 

## Support

For issues or questions:
- GitHub Issues: https://github.com/wolf2627/Agentic-RAG-App/issues
- Documentation: See `docs/` folder