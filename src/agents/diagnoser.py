from agents import Agent, function_tool, RunContextWrapper
from typing import Any
from .helper import load_instructions

# RAG imports
from src.rag.core.services import retrieve_context
from src.rag.api.dependencies import get_settings_dep, get_vector_store_dep, get_openai_client_dep

@function_tool
async def retrieve_medical_knowledge(ctx: RunContextWrapper[Any], query: str) -> str:
    """
    Retrieve relevant medical knowledge from the patient's medical records.
    Use this tool when you need additional medical information to make a diagnosis.
    
    Args:
        ctx: Context wrapper containing patient_id and other metadata
        query: The medical query to search for in the knowledge base
        
    Returns:
        str: Retrieved medical information with sources, or error message
    """
    try:
        # Get patient_id from context
        patient_id = None
        
        # Access context through ctx.context attribute
        if hasattr(ctx, 'context') and ctx.context:
            if isinstance(ctx.context, dict):
                patient_id = ctx.context.get('patient_id')
        
        if not patient_id:
            return "Error: Patient ID not available in context. Cannot retrieve medical records."
        
        # Call RAG service to retrieve context
        # Note: We need to initialize dependencies here since we're not in FastAPI
        settings = get_settings_dep()
        vector_store = get_vector_store_dep(settings)
        openai_client = get_openai_client_dep(settings)
        
        # Use the RAG service's retrieve_context function
        chunks = await retrieve_context(
            question=query,
            patient_id=patient_id,
            openai_client=openai_client,
            vector_store=vector_store,
            top_k=settings.top_k
        )
        
        if not chunks:
            return f"No relevant medical information found in the patient's records for this query."
        
        # Format the results with sources
        formatted_results = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get('source_path', 'Unknown')
            formatted_results.append(
                f"[Source {i}: {source} (relevance: {chunk.score:.2f})]\n{chunk.content}"
            )
        
        context = "\n\n---\n\n".join(formatted_results)
        
        return f"Retrieved medical information from patient {patient_id}'s records:\n\n{context}"
        
    except Exception as e:
        return f"Error retrieving medical knowledge: {str(e)}"

diagnoser_agent = Agent(
    name="Diagnoser",
    instructions=load_instructions("diagnoser"),
    tools=[retrieve_medical_knowledge],
    model="gpt-4o",
)