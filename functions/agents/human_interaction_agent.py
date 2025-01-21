from typing import Dict, Any, List
from langgraph.types import Command
from .types import prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

system_prompt = """You are the customer service representative for PartSelect, specializing in refrigerator and dishwasher parts. Your role is to:
1. Communicate directly with customers in a clear, professional manner
2. Format responses to be concise and helpful
3. Use bullet points for lists or steps
4. Include relevant part numbers and prices when available
5. Highlight important warnings or notes

Focus only on Refrigerator and Dishwasher related information.

--- 
Output:
Only output the response, no other text. Do NOT use any knowledge of PartSelect or external websites outside of the information provided in the conversation.
"""

human_interaction_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[]
)

def format_messages_for_llm(messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Convert messages to LangChain format."""
    formatted = []
    for msg in messages:
        if msg["role"] == "system":
            formatted.append(SystemMessage(content=msg["content"]))
        elif msg["role"] == "user":
            formatted.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted.append(AIMessage(content=msg["content"], name=msg.get("name")))
    return formatted

def human_interaction_node(state: State) -> Command[str]:
    try:
        logger.debug(f"State in human_interaction_node: {state}")
        
        # Format messages for LLM
        # formatted_messages = format_messages_for_llm(messages)
        
        # Generate response
        if state.get("pending_request"):
            info_needed = state.get("pending_request").get("request_info")
            response = human_interaction_agent.invoke(f"Other agents are requesting information about: {info_needed}. Use this state to respond to the user and ask for the information needed.")
        else:
            response = human_interaction_agent.invoke(state)
            
        logger.debug(f"Response in human_interaction_node: {response}")
        # Add our response to the messages, keeping only essential fields
        return Command(
            goto="supervisor",
            update={
                "messages": response["messages"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in human_interaction_node: {str(e)}")
        raise 