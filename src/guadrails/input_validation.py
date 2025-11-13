from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput
from pydantic import BaseModel

class SafetyCheck(BaseModel):
    is_safe: bool
    concerns: list[str]
    action: str

# Input validation
safety_agent = Agent(
    name="Safety Checker",
    instructions="""
    Check if the medical query is appropriate and safe to process.
    
    Flag concerns for:
    - Emergency situations (call emergency services)
    - Self-harm indicators
    - Dangerous medication requests
    - Inappropriate content
    
    Determine if query should proceed or be redirected.
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
    
    if not safety_check.is_safe:
        return GuardrailFunctionOutput(
            output_info=safety_check,
            tripwire_triggered=True,
        )
    
    return GuardrailFunctionOutput(
        output_info=safety_check,
        tripwire_triggered=False,
    )