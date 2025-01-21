from typing import Dict, Any, List
from langgraph.types import Command
from .types import prebuilt_llm, State, ValidationInfo
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from .agent_utils import process_agent_node, convert_dict_to_langchain_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

system_prompt = """
Your role is to validate any information provided by the user. You must ensure that a model exists, and if not, find suggestions for the user to provide a model number.
Similarly, you must ensure that a part number exists, and if not, find suggestions for the user to provide a part number.

Output must be structured exactly as:
{
    is_valid_or_compatible: true/false,
    found_item: "model_number" | "part_number" | null,
    item_suggestions: ["list", "of", "suggestions"]
}

Example Scenarios:
"How can I install part PS11752778?"
Steps:
    1) Use the use_search_feature tool to search for the part number
    2) Parse the html output to determine if a page was found with information about the part - use any other messages to help deduce this
    2) If the part number is found, set is_valid to true and found_item to "part_number"
    3) If the part number is not found, set is_valid to false and found_item to null
    4) Set item_suggestions to a list of suggestions for the user to provide a part number, based on the html output if the part is not found

Output:
{
    is_valid_or_compatible: false,
    found_item: null,
    item_suggestions: ["PS11752778"]
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
    tools=[],
)

def process_validation_responses(responses: Dict[str, Any], messages: List[BaseMessage]) -> ValidationInfo:
    """Process responses from other agents for validation."""
    process_messages = messages.copy()
    
    if data_response := responses.get("validation_agent_data"):
        process_messages.append(AIMessage(content=f"Data received from data agent: {data_response}"))
        process_messages.append(HumanMessage(content="Please validate this information."))
    
    return validation_agent.with_structured_output(ValidationInfo).invoke(process_messages)

def process_no_responses(messages: List[BaseMessage]) -> Dict[str, Any]:
    """Process when there are no responses from other agents."""
    # First pass - request data if needed
    planning_messages = messages + [
        HumanMessage(content="""In json format with keys need_data and plan. Do we need to fetch any data from the website to validate the information? If so \
                                    provide a structured plan including which tools to use and in what order and set need_data to true. \
                                    If not, set need_data to false.""")
    ]
    
    need_data = validation_agent.invoke(planning_messages)
    logger.debug(f"Validation agent data need: {need_data}")
    
    if need_data.get("need_data", False):
        # Create a data request
        data_request = {
            "requesting_agent": "validation_agent",
            "target_agent": "data_agent",
            "request": need_data,
            "response_needed": True
        }
        
        return Command(
            goto="data_agent",
            update={
                "messages": messages,
                "next": "data_agent",
                "agent_requests": [data_request],
                "agent_responses": {}
            }
        )
    
    return validation_agent.with_structured_output(ValidationInfo).invoke(messages)

def validation_agent_node(state: State) -> Command[str]:
    return process_agent_node(
        state=state,
        agent_name="validation_agent",
        agent_llm=validation_agent.with_structured_output(ValidationInfo),
        system_message=system_prompt,
        process_responses=process_validation_responses,
        process_no_responses=process_no_responses,
        default_next_agent="supervisor"
    )