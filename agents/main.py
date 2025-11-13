from agents import Agent, Runner
from dotenv import load_dotenv

from helper import load_instructions

load_dotenv()

agent = Agent(name="Assistant", instructions=load_instructions("assistant"))

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)