from typing import Dict, Any, List
from langgraph.types import Command
from .types import prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, BaseMessage

system_message = """You are a conversation summary agent for PartSelect's customer service system. Your role is to:
1. Summarize the conversation history concisely
2. Extract and organize key information like:
   - Part numbers mentioned
   - Model numbers mentioned
   - Customer issues/symptoms described
   - Any validated information from the validation agent
   - Any repair suggestions made
   - Any questions that still need answers
   - Current conversation state/progress

Format your response in a clear, structured way that helps other agents understand the context quickly.
Focus only on Refrigerator and Dishwasher related information.

Your output MUST be a JSON object with the following structure:
{
    "part_numbers": ["list", "of", "part", "numbers"] or null,
    "model_numbers": ["list", "of", "model", "numbers"] or null,
    "issues_reported": ["list", "of", "issues"] or null,
    "validated_info": ["list", "of", "validated", "information"] or null,
    "repair_suggestions": ["list", "of", "repair", "suggestions"] or null,
    "pending_questions": ["list", "of", "questions"] or null,
    "current_state": "description of current state",
    "conversation_summary": "2-3 sentence summary of the interaction so far"
}
"""

summary_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_message,
    tools=[],
)

def summary_agent_node(state: State) -> Command[str]:
    try:
        response = summary_agent.invoke(state)
        return Command(goto="supervisor", update={"messages": state["messages"] + [AIMessage(content=str(response))]})
    except Exception as e:
        logger.error(f"Error in summary_agent_node: {str(e)}")
        raise
