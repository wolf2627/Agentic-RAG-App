from agents import Agent, Runner, RunContextWrapper, handoff
from agents.handoffs import HandoffInputData
from agents.items import ItemHelpers, HandoffCallItem
from dotenv import load_dotenv
from pydantic import BaseModel
import json

from .helper import load_instructions

load_dotenv()

class LanguageConversionInput(BaseModel):
    input: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: LanguageConversionInput):
    print(f"Handoff called with translated input: {input_data.input}")

def custom_input_filter(handoff_data: HandoffInputData) -> HandoffInputData:
    """
    Filter that replaces the entire conversation history with just the translated English instruction.
    The haiku agent will only see the English instruction, not the original multilingual input.
    """
    # Find the HandoffCallItem which contains the tool call arguments with the translated text
    translated_input = None
    for item in handoff_data.new_items:
        if isinstance(item, HandoffCallItem):
            # Extract the 'input' field from the tool call arguments
            args = json.loads(item.raw_item.arguments)
            translated_input = args.get('input')
            break
    
    if translated_input:
        # Create a fresh conversation with ONLY the translated English instruction
        new_input_history = ItemHelpers.input_to_new_input_list(translated_input)
        
        # Return a modified HandoffInputData with the new clean history
        return handoff_data.clone(
            input_history=tuple(new_input_history),
            pre_handoff_items=(),  # Remove all previous conversation
            new_items=()  # Remove the handoff tool call from history
        )
    
    # Fallback: return original data if we couldn't extract the translation
    return handoff_data

# Haiku agent that generates haikus in English
haiku_agent = Agent(
    name="Haiku Agent", 
    instructions=load_instructions("assistant"), 
    model="gpt-4o-mini"
)


handoff_obj = handoff(
    agent=haiku_agent,
    on_handoff=on_handoff,
    input_type=LanguageConversionInput,
    input_filter=custom_input_filter,  # Add the input filter to replace conversation history
)


# Triage agent that handles multilingual input and delegates to haiku agent
triage_agent = Agent(
    name="Triage Agent",
    instructions=load_instructions("triage_agent"),
    handoffs=[handoff_obj],  # ✅ Use the handoff_obj with your customizations
    model="gpt-4o-mini",
)

# Test with Tamil input - the triage agent will translate it and hand off with English
user_input = "நிரலாக்கத்தில் மறுநிகழ்வு பற்றி ஒரு ஹைக்கூ எழுதுங்கள்."
print(f"User input (Tamil): {user_input}\n")

result = Runner.run_sync(triage_agent, user_input)
print(f"\nFinal output (English): {result.final_output}")