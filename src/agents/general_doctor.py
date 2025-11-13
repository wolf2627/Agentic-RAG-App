from agents import Agent
from pydantic import BaseModel
from helper import load_instructions

class QueryClassification(BaseModel):
    is_complex: bool
    category: str
    urgency_level: str
    reasoning: str

general_doctor_agent = Agent(
    name="General Doctor",
    instructions=load_instructions("general_doctor"),
    output_type=QueryClassification,
    handoffs=["ai_agent", "diagnoser_agent"],
    model="gpt-4.1-nano",
)