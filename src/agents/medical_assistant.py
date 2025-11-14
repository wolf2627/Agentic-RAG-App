from agents import Agent
from .helper import load_instructions
import os
from dotenv import load_dotenv

load_dotenv()

medical_assistant = Agent(
    name="Medical Assistant",
    instructions=load_instructions("medical_assistant"),
    model=os.getenv("MEDICAL_ASSISTANT_MODEL", "gpt-4.1-nano"),
)