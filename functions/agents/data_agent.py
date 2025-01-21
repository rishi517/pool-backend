from typing import Dict, Any, List
from langgraph.types import Command
from .types import prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from .agent_utils import process_agent_node, convert_dict_to_langchain_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from tools.request_tools import (
    use_search_feature_tool,
    check_part_compatibility_tool,
    search_instant_repairman_models_tool,
    get_instant_repairman_parts_tool,
    search_blog_posts_tool,
    general_dishwasher_repair_tips_tool,
    general_refrigerator_repair_tips_tool
)

system_message = """You are a data extraction agent for PartSelect's customer service system. Your role is to interface with the PartSelect website and provide structured data to other agents.

Your capabilities include:
1. Searching for parts and models using the search feature
2. Checking part compatibility with specific models
3. Finding common problems and repair solutions for models
4. Getting repair tips from blog posts and general guides
5. Extracting structured data from website responses

When responding:
1. Always structure your responses clearly
2. Include relevant URLs, part numbers, and model numbers
3. Format prices and availability information consistently
4. Note any compatibility issues or warnings
5. Include relevant repair tips or blog posts when available

Focus only on Refrigerator and Dishwasher related information.
OUTPUT ---:
You must reformat any HTML content into a structured format - keep any information that is relevant to refrigerators or dishwashers.
"""

data_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_message,
    tools=[
        use_search_feature_tool,
        check_part_compatibility_tool,
        search_instant_repairman_models_tool,
        get_instant_repairman_parts_tool,
        search_blog_posts_tool,
        general_dishwasher_repair_tips_tool,
        general_refrigerator_repair_tips_tool
    ],
)

def process_data_requests(messages: List[BaseMessage], agent_requests: List[Dict[str, Any]]) -> str:
    """Process direct requests for data."""
    request = [req for req in agent_requests if req["target_agent"] == "data_agent"][0]
    request_messages = messages + [HumanMessage(content=request["request"])]
    return data_agent.invoke(request_messages)

def process_no_responses(messages: List[BaseMessage]) -> Dict[str, Any]:
    """Process when there are no direct requests."""
    # Use LLM to determine what data to fetch and how to structure the response
    planning_messages = messages + [
        HumanMessage(content=
            "What data do we need to fetch from the website based on the conversation? " + 
            "Respond with a structured plan including which tools to use and in what order.")
    ]
    
    plan = data_agent.invoke(planning_messages)
    logger.debug(f"Data agent plan: {plan}")
    
    # Use LLM to execute the plan and format the response
    execution_messages = messages + [
        AIMessage(content=f"Here's my plan: {plan}"),
        HumanMessage(content="Execute this plan and format the results.")
    ]
    
    return data_agent.invoke(execution_messages)

def data_agent_node(state: State) -> Command[str]:
    # Process the request and get response
    result = process_agent_node(
        state=state,
        agent_name="data_agent",
        agent_llm=data_agent,
        system_message=system_message,
        process_responses=process_data_requests if state.get("agent_requests") else None,
        process_no_responses=process_no_responses,
        default_next_agent="supervisor"
    )
    
    # Always return to supervisor with updated state
    return Command(
        goto="supervisor",
        update={
            "messages": result.update["messages"],
            "agent_requests": state.get("agent_requests", []),  # Data agent doesn't create new requests
            "agent_responses": result.update.get("agent_responses", {})
        }
    )
     