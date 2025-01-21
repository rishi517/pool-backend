from typing import Dict, Any, List
from langgraph.types import Command
from lib.types import AgentRequest, prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from tools.request_tools import (
    use_search_feature_tool,
    check_part_compatibility_tool,
    search_instant_repairman_models_tool,
    get_instant_repairman_parts_tool,
    search_blog_posts_tool,
    general_dishwasher_repair_tips_tool,
    general_refrigerator_repair_tips_tool,
    request_page_tool
)

system_message = """You are a data extraction agent for PartSelect's customer service system. Your role is to interface with the PartSelect website and provide structured data to other agents.

Your capabilities include:
1. Searching for parts and models using the search feature (use_search_feature_tool)
2. Checking part compatibility with specific models (check_part_compatibility_tool)
3. Finding common problems and repair solutions for models (search_instant_repairman_models_tool)
4. Getting repair tips from blog posts and general guides (search_blog_posts_tool, general_dishwasher_repair_tips_tool, general_refrigerator_repair_tips_tool)
5. Extracting structured data from website responses (request_page_tool)


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
        general_refrigerator_repair_tips_tool,
        request_page_tool
    ],
)

def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    prompt = f"You have a pending request from the {pending_request.get('requesting_agent')} agent. Use the provided tools to provide a response. \
                      Use the information provided by  {pending_request.get('request_info')}  to respond to the user. Here is the general state of the conversation: {state}\
                      If a given number is ambigious, ask the user to clarify which number they are referring to."
    response = data_agent.invoke({"messages": prompt})
    pending_request = None
    return Command(
        goto="supervisor",
        update={
            "messages": state["messages"] + [AIMessage(content=str(response))],
            "pending_request": pending_request
        }
    )
     
def data_agent_node(state: State) -> Command[str]:
    try:
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
        response = data_agent.invoke(state)
        return Command(goto="supervisor", update={"messages": state["messages"] + [AIMessage(content=str(response))]})
    except Exception as e:
        logger.error(f"Error in data_agent_node: {str(e)}")
        raise
