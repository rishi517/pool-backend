import os
from typing import List, Literal, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langgraph.types import Command

from .product_search_agent import product_search_agent_node
from .product_info_agent import product_info_agent_node
from .store_search_agent import store_search_agent_node
from .store_info_agent import store_info_agent_node
from lib.types import prebuilt_llm, State, VALID_AGENT_REQUESTS, AgentRequest
from firebase_functions import logger
from .human_interaction_agent import human_interaction_node
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import Field

# Define our possible routes

supervisor_options = Literal["human_interaction", "product_search_agent", "product_info_agent", "store_search_agent", "store_info_agent", "end"]

class Router(TypedDict):
    next_agent: Literal["human_interaction", "product_search_agent", "product_info_agent", "store_search_agent", "store_info_agent", "end"]
    request_type: Optional[str] = Field(default="analyze", description="The type of request being made")
    request_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Information for the target agent to process the request")

system_prompt = """You are the workflow coordinator for Heritage Pool Plus's Pool Equipment Chat Agent. 
This chatbot handles user queries related to pool equipment, store details, and product information. The assistant must be able to determine the best way to
retrieve relevant data by interacting with multiple APIs and structuring responses in a way that's useful to the user.      

You must accurately and quickly triage the conversation to the correct agent. Keep the number of steps to a minimum.

Your role is to analyze conversations and determine which specialized agent should handle the next step:

1. human_interaction: Communicates directly with the user (MUST be the final step). 
    Use this agent if you need more information from the user not provided by the other agents. It is better to ask the user for information than to assume which action to take.

2. product_search_agent: The product search expert. Use this agent if the user is asking about product information, but you don't know which product they are referring to.

3. product_info_agent: The specific product expert. Use this agent if the user is asking about product information, and you know which product they are referring to.

4. store_search_agent: The store search expert. Use this agent if the user is asking about store information, but you don't know which store they are referring to.

5. store_info_agent: The specific store expert. Use this agent if the user is asking about store information, and you know which store they are referring to.

Rules:
1. ALWAYS end with human_interaction for user communication
2. When analyzing the output of an agent, look for a request. If the request must be fulfilled by the user, route to human_interaction.

Your response must be a JSON object with:
{
    "next_agent": string,  // The agent to route to
    "request_type": string,  // What you need from the agent
    "request_info": object   // Data needed for the request
}

If a user query does not relate to pool equipment, store details, or product information, then route to human_interaction with request_info including "This is not a relevant question"
"""

def validate_agent_request(request: AgentRequest) -> bool:
    """Validate if an agent is allowed to make a request to another agent."""
    if request["requesting_agent"] not in VALID_AGENT_REQUESTS:
        return False
    return request["target_agent"] in VALID_AGENT_REQUESTS[request["requesting_agent"]]

def analyze_conversation(messages: List[Dict[str, str]], current_agent: str) -> Router:
    """Analyze the conversation to determine the next step."""
    # Keep only the last N messages to prevent context overflow
    MAX_MESSAGES = 5
    recent_messages = messages[-MAX_MESSAGES:] if len(messages) > MAX_MESSAGES else messages
    
    # Convert messages to LangChain format
    formatted_messages = []
    for msg in recent_messages:
        if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)):
            formatted_messages.append(msg)
        else:
            # Truncate very long messages
            content = msg["content"]

                
            if msg["role"] == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=content))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=content, name=msg.get("name")))

    analysis_messages = [
        SystemMessage(content=system_prompt)
    ] + formatted_messages + [HumanMessage(content="Please respond with a JSON : {next_agent: string, request_type: string, request_info: object}. Avoid \
        calling the {current_agent} agent again as next_agent unless you want to use another tool. We want to emphasize speed and efficiency, so minimize the number of steps by listing out the steps you will take to solve the problem.")]
    logger.debug(f"Analysis messages: {analysis_messages}")
    # Use structured output to ensure we get a dictionary
    response = prebuilt_llm.with_structured_output(Router).invoke(analysis_messages)
    return response

def supervisor_node(state: State) -> Command[str]:
    try:
        logger.debug(f"Supervisor node state: {state}")
        current_agent = state.get("current_agent")
        pending_request = state.get("pending_request", None)
        logger.debug(f"Pending request: {pending_request}")
        # If we just came from human_interaction, end the flow
        if current_agent == "human_interaction":
            return Command(goto=END, update=state)
            
        # Process any pending requests
        if pending_request:
            request = pending_request
            
            # Validate the request
            if not validate_agent_request(request):
                logger.error(f"Invalid request from {request['requesting_agent']} to {request['target_agent']}")
                # Route to human_interaction with error
                return Command(
                    goto="human_interaction",
                    update={
                        **state,
                        "current_agent": "human_interaction",
                        "pending_request": None,
                        "conversation_state": {
                            **state.get("conversation_state", {}),
                            "error": f"Invalid request from {request['requesting_agent']}"
                        }
                    }
                )
            
            # Route to the target agent
            return Command(
                goto=request["target_agent"],
                update={
                    **state,
                    "current_agent": request["target_agent"],
                    "pending_request": None
                }
            )
        
        # No pending requests, analyze conversation for next step
        analysis = analyze_conversation(state["messages"], current_agent)
        logger.debug(f"Analysis: {analysis}")
        next_agent = analysis["next_agent"]
        if next_agent == current_agent:
            next_agent = "human_interaction"
        
        return Command(
            goto=next_agent,
            update={
                **state,
                "current_agent": next_agent
            }
        )
        
    except Exception as e:
        logger.error(f"Error in supervisor_node: {str(e)}")
        raise

def build_supervisor_graph():
    builder = StateGraph(State)
    
    # Add nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("human_interaction", human_interaction_node)
    builder.add_node("product_search_agent", product_search_agent_node)
    builder.add_node("product_info_agent", product_info_agent_node)
    builder.add_node("store_search_agent", store_search_agent_node)
    builder.add_node("store_info_agent", store_info_agent_node)
    # START always goes to supervisor
    builder.add_edge(START, "supervisor")
    
    
    

    
    return builder.compile()
