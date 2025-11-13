from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput
from pydantic import BaseModel
from src.agents.helper import load_instructions

class SafetyCheck(BaseModel):
    is_safe: bool
    is_emergency: bool
    concerns: list[str]
    action: str

# Input validation
safety_agent = Agent(
    name="Safety Checker",
    instructions="""
    Check if the medical query is appropriate and safe to process.
    
    Classify the query:
    1. is_safe: Can we process this query? (Only false for harmful/inappropriate content)
    2. is_emergency: Is this a medical emergency requiring immediate action?
    
    Flag as NOT SAFE (is_safe=false) ONLY for:
    - Self-harm or suicide ideation
    - Requests for dangerous/illegal substances
    - Inappropriate/abusive content
    - Requests to harm others
    
    Flag as EMERGENCY (is_emergency=true) for:
    - Heart attack, stroke, severe chest pain
    - Difficulty breathing, choking
    - Severe bleeding, major trauma
    - Loss of consciousness
    - Severe allergic reactions
    
    For emergencies, set is_safe=true (we should still provide guidance) 
    but is_emergency=true (we'll add emergency warnings).
    
    Provide appropriate action recommendation.
    """,
    output_type=SafetyCheck
)

@input_guardrail
async def input_safety_guardrail(ctx, agent, input_data):
    """Validate input before processing"""
    result = await Runner.run(
        safety_agent,
        input_data,
        context=ctx.context
    )
    
    safety_check = result.final_output_as(SafetyCheck)
    
    # Store the safety check in context for later use
    if hasattr(ctx, 'context') and ctx.context:
        # Attach safety info to context if possible
        pass
    
    # Only trigger tripwire for truly unsafe content, not emergencies
    if not safety_check.is_safe:
        return GuardrailFunctionOutput(
            output_info=safety_check,
            tripwire_triggered=True,
        )
    
    # For emergencies, pass through but include the info
    return GuardrailFunctionOutput(
        output_info=safety_check,
        tripwire_triggered=False,
    )