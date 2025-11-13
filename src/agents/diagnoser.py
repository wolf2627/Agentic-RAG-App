from agents import Agent, function_tool
from agents.run_context import RunContext
from helper import load_instructions

@function_tool
async def retrieve_medical_knowledge(query: str, context: RunContext) -> str:
    """Retrieve relevant medical knowledge from RAG system."""
    # RAG implementation
    pass

diagnoser_agent = Agent(
    name="Diagnoser",
    instructions=load_instructions("diagnoser"),
    tools=[retrieve_medical_knowledge],
    model="gpt-4o",
)