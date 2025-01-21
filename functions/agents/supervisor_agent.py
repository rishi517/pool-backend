import os
from typing import List, Literal, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langgraph.types import Command

from .blog_agent import blog_agent_node
from .repair_agent import repair_agent_node
from .validation_agent import validation_agent_node
from lib.types import prebuilt_llm, State, VALID_AGENT_REQUESTS, AgentRequest
from firebase_functions import logger
from .human_interaction_agent import human_interaction_node
from .data_agent import data_agent_node
from .summary_agent import summary_agent_node
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import Field

# Define our possible routes
members = Literal["repair_agent", "validation_agent", "human_interaction", "data_agent", "blog_agent"]
options = Literal["repair_agent", "validation_agent", "human_interaction", "data_agent", "blog_agent", "end"]
supervisor_options = Literal["repair_agent", "validation_agent", "human_interaction", "data_agent", "blog_agent", "__end__"]

class Router(TypedDict):
    next_agent: Literal["repair_agent", "validation_agent", "human_interaction", "data_agent", "blog_agent", "end"]
    request_type: Optional[str] = Field(default="analyze", description="The type of request being made")
    request_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Information for the target agent to process the request")

system_prompt = """You are the workflow coordinator for PartSelect's customer service system. 
You must accurately and quickly triage the conversation to the correct agent. Keep the number of steps to a minimum.
Your role is to analyze conversations and determine which specialized agent should handle the next step:

1. validation_agent: Validates part/model numbers and checks compatibility. There is no need to validate data you got from other agents, and only validate individual parts and models if the user wants to.
2. repair_agent: Provides repair solutions and part recommendations. Use this agent when the user mentions a problem and you need to provide a solution.
3. data_agent: Fetches product data and specifications. You cannot request this agent unless another agent has requested it. You cannot request this agent individually.
4. blog_agent: Searches blog posts for general information and tips. Use this agent when the user asks general questions about appliance maintenance, common issues, or best practices for dishwasher and refrigerator repair.
5. human_interaction: Communicates directly with the user (MUST be the final step). 
    Use this agent if you need more information from the user not provided by the other agents. It is better to ask the user for information than to assume which action to take.

Rules:
1. ALWAYS end with human_interaction for user communication
2. When analyzing the output of an agent, look for a request. If the request must be fulfilled by the user, route to human_interaction.
3. Use blog_agent for general questions that don't require specific model numbers or parts
4. Use repair_agent when the user has a specific problem that needs fixing

Your response must be a JSON object with:
{
    "next_agent": string,  // The agent to route to
    "request_type": string,  // What you need from the agent
    "request_info": object   // Data needed for the request
}
"""

def validate_agent_request(request: AgentRequest) -> bool:
    """Validate if an agent is allowed to make a request to another agent."""
    if request["requesting_agent"] not in VALID_AGENT_REQUESTS:
        return False
    return request["target_agent"] in VALID_AGENT_REQUESTS[request["requesting_agent"]]

def analyze_conversation(messages: List[Dict[str, str]], current_agent: str) -> Router:
    """Analyze the conversation to determine the next step."""
    # Convert messages to LangChain format
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)):
            formatted_messages.append(msg)
        else:
            if msg["role"] == "system":
                formatted_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"], name=msg.get("name")))

    analysis_messages = [
        SystemMessage(content=system_prompt)
    ] + formatted_messages + [HumanMessage(content="Please respond with a JSON object with the following structure: {next_agent: string, request_type: string, request_info: object}. Avoid \
        calling the {current_agent} agent again as next_agent unless you want to use another tool. We want to emphasize speed and efficiency.")]
    logger.debug(f"Analysis messages: {analysis_messages}")
    # Use structured output to ensure we get a dictionary
    response = prebuilt_llm.with_structured_output(Router).invoke(analysis_messages)
    logger.debug(f"Response from analyze_conversation: {response}")
    
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
    builder.add_node("repair_agent", repair_agent_node)
    builder.add_node("validation_agent", validation_agent_node)
    builder.add_node("data_agent", data_agent_node)
    builder.add_node("blog_agent", blog_agent_node)
    # START always goes to supervisor
    builder.add_edge(START, "supervisor")
    

    
    return builder.compile()
