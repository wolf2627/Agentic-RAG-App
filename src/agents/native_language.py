from agents import Agent
from .helper import load_instructions
import os
from dotenv import load_dotenv

load_dotenv()

native_language_agent = Agent(
    name="Response Translator",
    instructions=load_instructions("native_language"),
    model=os.getenv("NATIVE_LANGUAGE_MODEL", "gpt-4.1-nano"),
)