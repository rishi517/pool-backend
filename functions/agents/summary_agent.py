from typing import Dict, Any, List
from langgraph.types import Command
from .types import prebuilt_llm, State, MessageSummary
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from .agent_utils import process_agent_node, convert_dict_to_langchain_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

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

def process_summary_responses(responses: Dict[str, Any], messages: List[BaseMessage]) -> str:
    """Process direct requests for summary."""
    process_messages = messages.copy()
    
    # Process and clean up responses
    request = [req for req in responses if req.startswith("summary_agent_")][0]
    process_messages.append(HumanMessage(content=responses[request]))
    responses.pop(request)
    
    return summary_agent.invoke(process_messages)

def process_no_responses(messages: List[BaseMessage]) -> str:
    """Process when there are no direct requests."""
    analysis_messages = messages + [
        HumanMessage(content="Please analyze the conversation history between the USER and the AGENT and provide a structured summary. Ignore system messages.")
    ]
    
    return summary_agent.invoke(analysis_messages)

def summary_agent_node(state: State) -> Command[str]:
    # Remove half of the first messages to keep context manageable
    state["messages"] = state["messages"][len(state["messages"]) // 2:]
    
    # Process the request and get response
    result = process_agent_node(
        state=state,
        agent_name="summary_agent",
        agent_llm=summary_agent,
        system_message=system_message,
        process_responses=process_summary_responses,
        process_no_responses=process_no_responses,
        default_next_agent="supervisor"
    )
    
    # Always return to supervisor with updated state
    return Command(
        goto="supervisor",
        update={
            "messages": result.update["messages"],
            "agent_requests": state.get("agent_requests", []),  # Summary agent doesn't create new requests
            "agent_responses": result.update.get("agent_responses", {})
        }
    ) 