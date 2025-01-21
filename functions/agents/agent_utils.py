from typing import Dict, Any, List, Optional, Callable
from langgraph.types import Command
from .types import State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

def convert_dict_to_langchain_messages(messages: List[Dict[str, str]]) -> List[BaseMessage]:
    """Convert dictionary messages to LangChain message format."""
    converted_messages = []
    for msg in messages:
        if isinstance(msg, (AIMessage, HumanMessage, SystemMessage)):
            converted_messages.append(msg)
        else:
            if msg["role"] == "system":
                converted_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                converted_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "user":
                converted_messages.append(HumanMessage(content=msg["content"]))
    return converted_messages

def process_agent_node(
    state: State,
    agent_name: str,
    agent_llm: Any,
    system_message: str,
    process_responses: Optional[Callable[[Dict[str, Any], List[BaseMessage]], Any]] = None,
    process_no_responses: Optional[Callable[[List[BaseMessage]], Any]] = None,
    default_next_agent: str = "supervisor"
) -> Command[str]:
    """
    Shared logic for processing agent nodes in the workflow.
    
    Args:
        state: The current state
        agent_name: Name of the current agent
        agent_llm: The LLM instance for this agent
        system_message: System message for the agent
        process_responses: Optional callback for processing responses
        process_no_responses: Optional callback for when there are no responses
        default_next_agent: Default agent to route to if not specified
    """
    try:
        # Convert messages to LangChain format
        messages = convert_dict_to_langchain_messages([
            {"role": "system", "content": system_message},
        ] + state["messages"])
        
        try:
            # Check for responses from other agents
            agent_responses = state.get("agent_responses", {})
            agent_requests = state.get("agent_requests", [])
            
            # Get all responses for this agent
            relevant_responses = {
                key: value for key, value in agent_responses.items() 
                if key.startswith(f"{agent_name}_")
            }
            
            if relevant_responses and process_responses:
                # Process responses using the callback
                logger.debug(f"Processing responses for {agent_name}")
                response = process_responses(relevant_responses, messages)
                logger.debug(f"{agent_name} response with data: {response}")
                
                # Clear processed responses
                for key in relevant_responses.keys():
                    agent_responses.pop(key)
            else:
                # No responses to process, use the no_responses callback if provided
                logger.debug(f"No responses to process for {agent_name}")
                if process_no_responses:
                    logger.debug(f"Processing no responses for {agent_name}")
                    response = process_no_responses(messages)
                    logger.debug(f"{agent_name} response with no data: {response}")
                else:
                    logger.debug(f"Invoking {agent_name} without responses")
                    response = agent_llm.invoke(messages)
                logger.debug(f"{agent_name} response: {response}")
            
            # Add the response to messages
            agent_message = AIMessage(content=str(response))
            
            # Convert messages back to dict format for state
            state_messages = state["messages"] + [{
                "role": "assistant",
                "name": agent_name,
                "content": agent_message.content
            }]
            
            # Get the next agent - either from state or use default
            next_agent = state.get("next", default_next_agent)
            
            return Command(
                goto=next_agent,
                update={
                    "messages": state_messages,
                    "next": next_agent,
                    "agent_requests": agent_requests,
                    "agent_responses": agent_responses
                }
            )
            
        except Exception as e:
            logger.error(f"Error in {agent_name} processing: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error in {agent_name}_node: {str(e)}")
        raise 