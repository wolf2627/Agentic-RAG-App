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

# if __name__ == "__main__":
#     # Testing the translator agent
#     user_input = "எனக்கு ரெண்டு நாளா காய்ச்சல் இருக்கு."
#     result = Runner.run_sync(translator_agent, user_input)
#     print(result.final_output)