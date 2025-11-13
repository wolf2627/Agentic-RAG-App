from agents import Agent, Runner
from dotenv import load_dotenv

# absolute import when running as script, relative when imported as module
try:
    from .helper import load_instructions
except ImportError:
    from helper import load_instructions

load_dotenv()

translator_agent = Agent(
    name="Translator",
    instructions=load_instructions("translator"),
    model="gpt-4.1-nano",
)

from agents import Agent, Runner
from dotenv import load_dotenv

# Use absolute import when running as script, relative when imported as module
try:
    from .helper import load_instructions
    from src.models.model import TranslatedQuery
except ImportError:
    from helper import load_instructions
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.models.model import TranslatedQuery

load_dotenv()

translator_agent = Agent(
    name="Translator",
    instructions=load_instructions("translator"),
    output_type=TranslatedQuery,  # Return structured output with detected language
    model="gpt-4.1-nano",
)

if __name__ == "__main__":
    # Testing the translator agent
    user_input = "எனக்கு ரெண்டு நாளா காய்ச்சல் இருக்கு."
    result = Runner.run_sync(translator_agent, user_input)
    print(f"Detected Language: {result.final_output.detected_language}")
    print(f"Language Code: {result.final_output.language_code}")
    print(f"Translation: {result.final_output.translated_text}")
    print(f"Confidence: {result.final_output.confidence}")