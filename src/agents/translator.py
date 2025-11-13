from agents import Agent, Runner
from helper import load_instructions
from dotenv import load_dotenv

load_dotenv()

translator_agent = Agent(
    name="Translator",
    instructions=load_instructions("translator"),
    model="gpt-4.1-nano",
)

# Testing the translator agent
# user_input = "எனக்கு ரெண்டு நாளா காய்ச்சல் இருக்கு."
# result = Runner.run_sync(translator_agent, user_input)
# print(result.final_output)