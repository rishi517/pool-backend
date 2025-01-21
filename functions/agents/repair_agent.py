from typing import Dict, Any, List, Optional
from langgraph.types import Command
from .types import prebuilt_llm, State, AgentRequest, RepairInfo
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

system_prompt = """You are the repair agent for PartSelect's customer service system. Your role is to:
1. Identify repair needs based on model numbers and symptoms
2. Find appropriate parts for repairs
3. Provide repair instructions and tips
4. Track what information is still needed

You follow PartSelect's Instant Repairman process. Thus, these steps must be performed consecutively. Track the completion of each step in your state.
1. Retrieve model number from user
2. Validate the model number with the validation_agent and retrieve model data from data_agent
3. Show the user list of common problems from the model data
4. Retrieve the problem from the user
5. Retrieve the parts that most commonly fix the problem that was selected by the user
6. Utilize the data_agent to get any other repair instructions and tips

Your output MUST be a JSON object with the following structure:
{
    "provided_model_number": boolean,
    "list_of_problems": ["list", "of", "problems"] or null,
    "provided_problem": "specific problem mentioned" or null,
    "list_of_parts": ["list", "of", "parts"] or null,
    "info_needed": an AgentRequest object
}
An AgentRequest object is a JSON object with the following structure:
{
    "requesting_agent": "agent name", // The agent that is requesting the information (repair_agent)
    "target_agent": "agent name", // The agent that is providing the information (data_agent, validation_agent, summary_agent, human_interaction)
    "request_type": "request type", // The type of request (e.g. "model_number", "problem", "part", "info")
    "request_info": "request info" // The information needed for the request 
}

Before providing repair suggestions:
1. Ensure model numbers are validated
2. Consider getting a conversation summary if context is unclear

Focus only on Refrigerator and Dishwasher repairs. If you need information from the user, request it from the human_interaction agent.
"""

repair_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[],
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

def repair_agent_node(state: State) -> Command[str]:
    try:
        logger.debug(f"State in repair_agent_node: {state}")
        
        # First, analyze if we need any information
        analysis = analyze_repair_needs(state)
        response = analysis.get("structured_response")
        logger.debug(f"Analyze Response in repair_agent_node: {response}")
        if response.get("info_needed"):
            return Command(
                goto="supervisor",
                update={
                    "messages": state["messages"] + [AIMessage(content=response["info_needed"].get("request_info"))],
                    "pending_request": response["info_needed"]
                }
            )
        
            
        # If we have all needed information, generate repair guidance
        response = repair_agent.invoke(state)
        logger.debug(f"Response in repair_agent_node: {response}")
        
        return Command(
            goto="supervisor",
            update={
                "messages": response["messages"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in repair_agent_node: {str(e)}")
        raise

