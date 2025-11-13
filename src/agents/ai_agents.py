from agents import Agent
from helper import load_instructions

ai_agent = Agent(
    name="AI Agent",
    instructions=load_instructions("ai_agent"),
    model="gpt-4.1-nano",
)