from agents import Agent
from src.models.model import QueryClassification
from src.guadrails import input_safety_guardrail
from .helper import load_instructions

# This agent only classifies queries, it doesn't hand off
# The routing logic is handled in main.py
triage_nurse = Agent(
    name="Triage Nurse",
    instructions=load_instructions("triage_nurse"),
    output_type=QueryClassification,
    # Removed handoffs - we'll handle routing in main.py instead
    input_guardrails=[input_safety_guardrail],
    model="gpt-4.1-nano",
)