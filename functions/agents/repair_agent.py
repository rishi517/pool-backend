from typing import Dict, Any, List, Optional
from langgraph.types import Command
from lib.types import prebuilt_llm, State, AgentRequest, RepairInfo
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.request_tools import search_instant_repairman_models_tool, get_instant_repairman_parts_tool, request_page_tool, general_dishwasher_repair_tips_tool, general_refrigerator_repair_tips_tool

system_prompt = """You are the repair agent for PartSelect's customer service system. Your role is to:
1. Identify repair needs based on model numbers and symptoms
2. Find appropriate parts for repairs
3. Provide repair instructions and tips
4. Track what information is still needed

You may not use any knowledge of PartSelect or external websites outside of the information provided in the conversation by either the user or the other agents.

For model specific repairs, follow PartSelect's Instant Repairman process. Thus, these steps must be performed consecutively. Track the completion of each step in your state.
1. Retrieve model number from user
2. Validate the model number with the validation_agent
3. Search for model data directly using search_instant_repairman_models_tool
4. Show the user list of common problems from the model data
5. Retrieve the problem from the user
6. Get parts that most commonly fix the problem using get_instant_repairman_parts_tool
7. Get repair instructions and tips using request_page_tool

Other tools:
1. general_dishwasher_repair_tips_tool - Use this tool to get general repair tips for dishwashers
2. general_refrigerator_repair_tips_tool - Use this tool to get general repair tips for refrigerators

Only use the data_agent as a fallback if the direct tools fail or return insufficient information.

Your output MUST be a JSON object with the following structure:
{
    "provided_model_number": boolean,
    "list_of_problems": ["list", "of", "problems"] or null,
    "provided_problem": "specific problem mentioned" or null,
    "list_of_parts": ["list", "of", "parts"] or null,
    "info_needed": an AgentRequest object. If you need information from the user, request it from the human_interaction agent.
}
An AgentRequest object is a JSON object with the following structure:
{
    "requesting_agent": "agent name", // The agent that is requesting the information (repair_agent)
    "target_agent": "agent name", // The agent that is providing the information (data_agent, validation_agent, human_interaction)
    "request_type": "request type", // The type of request (e.g. "model_number", "problem", "part", "info")
    "request_info": "request info" // The information needed for the request be as descriptive as possible and provide any additional context/values
}

Focus only on Refrigerator and Dishwasher repairs.
"""

repair_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[search_instant_repairman_models_tool, get_instant_repairman_parts_tool, request_page_tool, general_dishwasher_repair_tips_tool, general_refrigerator_repair_tips_tool],
    response_format=RepairInfo
)

def analyze_repair_needs(state: State) -> RepairInfo:
    """Analyze the conversation to determine if we need information from other agents."""
    try:
        # Add analysis prompt to the messages
        
        analysis_messages = {"messages": state["messages"] + [
            HumanMessage(content="""Analyze the conversation and determine what information we need to proceed with repair guidance.
            Return a JSON object with:
            - Whether a model number is provided
            - Any problems mentioned
            - Any parts mentioned
            - What additional information is needed""")
        ]}
        
        # Get structured analysis
        analysis = repair_agent.invoke(analysis_messages)
        return analysis
        
    except Exception as e:
        logger.error(f"Error in analyze_repair_needs: {str(e)}")
        raise
    
def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    try:
        prompt = f"You have a pending request from the {pending_request.get('requesting_agent')} agent.\
                      Use the information provided by  {pending_request.get('request_info')}  to respond to the user. Here is the general state of the conversation: {state}"
        response = repair_agent.invoke({"messages": prompt})
        structured_response = response.get("structured_response")
        if structured_response:
            if structured_response.get("info_needed"):
                pending_request = structured_response.get("info_needed")
            else:
                pending_request = None
            return Command(
                goto="supervisor",
                update={
                    "messages": state["messages"] + [AIMessage(content=str(structured_response))],
                    "pending_request": pending_request
                }
            )
        return Command(
            goto="supervisor",
            update={
                "messages": state["messages"] + [AIMessage(content=response)],
                "pending_request": pending_request
            }
        )
    except Exception as e:
        logger.error(f"Error in handle_pending_request: {str(e)}")
        raise

def repair_agent_node(state: State) -> Command[str]:
    try:
        logger.debug(f"State in repair_agent_node: {state}")
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
            
        # First, analyze if we need any information
        analysis = analyze_repair_needs(state)
        structured_response = analysis.get("structured_response")
        logger.debug(f"Analyze Response in repair_agent_node: {structured_response}")
        if structured_response and structured_response.get("info_needed"):
            return Command(
                goto="supervisor",
                update={
                    "messages": state["messages"] + [AIMessage(content=structured_response["info_needed"].get("request_info"))],
                    "pending_request": structured_response["info_needed"]
                }
            )
        
            
        # If we have all needed information, generate repair guidance
        response = repair_agent.invoke(state)
        logger.debug(f"Response in repair_agent_node: {response}")
        
        return Command(
            goto="supervisor",
            update={
                **state,
                "messages": response["messages"],
                "pending_request": None
            }
        )
        
    except Exception as e:
        logger.error(f"Error in repair_agent_node: {str(e)}")
        raise

