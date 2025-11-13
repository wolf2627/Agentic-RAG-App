from agents import Agent, function_tool, RunContextWrapper
from typing import Any
from .helper import load_instructions

@function_tool
async def retrieve_medical_knowledge(ctx: RunContextWrapper[Any], query: str) -> str:
    """Retrieve relevant medical knowledge from RAG system."""
    # RAG implementation
    pass

diagnoser_agent = Agent(
    name="Diagnoser",
    instructions=load_instructions("diagnoser"),
    tools=[retrieve_medical_knowledge],
    model="gpt-4o",
)