from typing import Dict, Any, List
from langgraph.types import Command
from lib.types import AgentRequest, prebuilt_llm, State, ValidationInfo
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from tools.request_tools import check_part_compatibility_tool, use_search_feature_tool
system_prompt = """
Your role is to validate any information provided by the user. You must ensure that a model exists, and if not, find suggestions for the user to provide a model number.
Similarly, you must ensure that a part number exists, and if not, find suggestions for the user to provide a part number. There is no need to validate data you got from other agents.
1) Only check for compatibility of a part with a model if the user specifically asks you to.
2) Use your tools (use_search_feature_tool and check_part_compatibility_tool) directly to perform these tasks.

REQUESTABLE AGENTS:
- data_agent: Only request help from this agent if your tools return unclear or invalid results
- human_interaction: Only use this agent if you need clarification from the user

Output must be structured exactly as:
{
    answer: "true" or "false" or "a description of the result",
    found_item: a detailed description of the item found, only set if we are searching for a part or model,
    item_suggestions: ["list", "of","detailed", "suggestions"]
    "info_needed": an AgentRequest object. If you need information from the user, request it from the human_interaction agent.
}

An AgentRequest object is a JSON object with the following structure:
{
    "requesting_agent": "agent name", // The agent that is requesting the information (repair_agent)
    "target_agent": "agent name", // The agent that is providing the information (data_agent, human_interaction)
    "request_type": "request type", // The type of request (e.g. "compatability", "part_exists", "model_exists")
    "request_info": "request info" // The information needed for the request be as descriptive as possible and provide any additional context/values
}

Example Scenarios:
"How can I install part PS11752778?"
Steps:
    1) Use the use_search_feature tool in the data_agent to search for the part number
    2) Parse the html output to determine if a page was found with information about the part - use any other messages to help deduce this
    2) If the part number is found, set is_valid to true and found_item to "part_number"
    3) If the part number is not found, set is_valid to false and found_item to null
    4) Set item_suggestions to a list of suggestions for the user to provide a part number, based on the html output if the part is not found

Output:
{
    answer: "false",
    found_item: null,
    item_suggestions: ["PS11752778"]
    info_needed: {
        "requesting_agent": "repair_agent",
        "target_agent": "validation_agent",
        "request_type": "part_exists",
        "request_info": "PS11752778"
    }
}

"Is this part compatible with WDT780SAEM1?"
Steps:
    1) Ensure that both the model number and part number are provided and run through the steps above to ensure they are valid
    2) Once you know they are valid, use the check_part_compatibility tool to check if the part is compatible with the model
    3) If the part is compatible, set is_valid_or_compatible to true and found_item to "part_number"
    4) If the part is not compatible, set is_valid_or_compatible to false and found_item to null
    5) Set item_suggestions to a list of suggestions for the user to provide a part number, based on the html output if the part is not compatible
"""

validation_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[check_part_compatibility_tool, use_search_feature_tool],
    response_format=ValidationInfo
)


def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    try:
        prompt = f"You have a pending request from the {pending_request.get('requesting_agent')} agent. \
                      Use the information provided by  {pending_request.get('request_info')}  to respond to the user. Here is the general state of the conversation: {state}\
                      If a given number is ambigious, ask the user to clarify which number they are referring to."
        response = validation_agent.invoke({"messages": prompt})
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
                "pending_request": None
            }
        )
    except Exception as e:
        logger.error(f"Error in handle_pending_request: {str(e)}")
        raise

def validation_agent_node(state: State) -> Command[str]:
    try:
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
        
        response = validation_agent.invoke(state)
        structured_response = response.get("structured_response")
        logger.debug(f"Response in validation_agent_node: {response}")
        return Command(
            goto="supervisor",
            update={
                **state,
                "messages": state["messages"] + [AIMessage(content=str(structured_response))],
                "pending_request": structured_response.get("info_needed")
            }
        )
    except Exception as e:
        logger.error(f"Error in validation_agent_node: {str(e)}")
        raise
