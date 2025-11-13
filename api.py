from fastapi import FastAPI, HTTPException
from src.main import process_patient_query
from src.models.model import PatientQuery
import traceback

app = FastAPI(title="Medical AI System")

@app.post("/query")
async def handle_query(query: PatientQuery):
    try:
        result = await process_patient_query(query)
        return result
    except Exception as e:
        # Log the full traceback for debugging
        print("=" * 80)
        print("ERROR in /query endpoint:")
        print(traceback.format_exc())
        print("=" * 80)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}