from agents import Agent, function_tool, RunContextWrapper
from typing import Any
from .helper import load_instructions

# RAG imports
from src.rag.core.services import retrieve_context
from src.rag.api.dependencies import get_settings_dep, get_vector_store_dep, get_openai_client_dep

@function_tool
async def check_patient_safety(ctx: RunContextWrapper[Any], query: str) -> str:
    """
    Check patient's allergies and medications for safety concerns.
    ALWAYS called before answering medication/treatment questions.
    
    Args:
        ctx: Context wrapper containing patient_id and other metadata
        query: The medication or treatment query to check for safety concerns
        
    Returns:
        str: Safety information including allergies, current medications, and potential contraindications
    """
    try:
        # Get patient_id from context
        patient_id = None
        
        # Access context through ctx.context attribute
        if hasattr(ctx, 'context') and ctx.context:
            if isinstance(ctx.context, dict):
                patient_id = ctx.context.get('patient_id')
        
        if not patient_id:
            return "Error: Patient ID not available in context. Cannot retrieve safety information."
        
        # Fetch critical safety data from RAG
        safety_query = f"""
        For patient {patient_id}, retrieve:
        1. ALL known allergies (especially drug allergies)
        2. Current medications and dosages
        3. Recent adverse reactions or contraindications
        4. Medical conditions that may affect medication use
        
        Query context: {query}
        """
        
        # Initialize RAG dependencies
        settings = get_settings_dep()
        vector_store = get_vector_store_dep(settings)
        openai_client = get_openai_client_dep(settings)
        
        # Use RAG to fetch safety data with focused retrieval
        chunks = await retrieve_context(
            question=safety_query,
            patient_id=patient_id,
            openai_client=openai_client,
            vector_store=vector_store,
            top_k=5  # Focused retrieval for critical safety information
        )
        
        if not chunks:
            return f"No safety information found in patient {patient_id}'s records. CAUTION: Recommend consulting healthcare provider before proceeding with any medication or treatment."
        
        # Format safety information from retrieved chunks
        safety_info = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get('source_path', 'Unknown')
            safety_info.append(
                f"[Source {i}: {source} (relevance: {chunk.score:.2f})]\n{chunk.content}"
            )
        
        formatted_safety_data = "\n\n---\n\n".join(safety_info)
        
        return f"""
PATIENT SAFETY INFORMATION (Patient ID: {patient_id}):

{formatted_safety_data}

INSTRUCTIONS FOR SAFETY ANALYSIS:
1. Review all allergies mentioned above - especially drug allergies
2. Check current medications for potential interactions
3. Identify any contraindications with the patient's query: "{query}"
4. If SAFE: Provide guidance with precautions
5. If CONTRAINDICATED: Clearly warn and suggest alternatives
6. If UNCERTAIN: Recommend consulting healthcare provider

Remember: Always err on the side of caution with patient safety.
"""
        
    except Exception as e:
        return f"Error retrieving patient safety information: {str(e)}. CRITICAL: Do not provide medication recommendations without safety verification. Recommend consulting healthcare provider."

safety_agent = Agent(
    name="Medication Safety Specialist",
    instructions=load_instructions("safety_agent"),
    tools=[check_patient_safety],
    model="gpt-4.1-nano",
)