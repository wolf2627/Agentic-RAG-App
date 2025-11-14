from agents import Agent
from .helper import load_instructions

medical_assistant = Agent(
    name="Medical Assistant",
    instructions=load_instructions("medical_assistant"),
    model="gpt-4.1-nano",
)