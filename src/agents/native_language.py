from agents import Agent
from helper import load_instructions

native_language_agent = Agent(
    name="Native Language Translator",
    instructions=load_instructions("native_language"),
    model="gpt-4.1-nano",
)