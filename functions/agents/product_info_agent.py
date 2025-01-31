from typing import Dict, Any, List
from langgraph.types import Command
from lib.types import AgentRequest, AgentResponse, ProductInfo, prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from tools.product_tools import search_klevu_products_tool, search_azure_products_tool, get_product_details_tool, get_pricing_tool, get_availability_tool


system_message = """You are a the product expert agent for Heritage Pool's customer service system. 

Minimize the number of tools you use.

Your capabilities include:
1. Getting product details for a specific product id (get_product_details_tool), THIS DOES NOT INCLUDE PRICING OR AVAILABILITY. If you want the pricing or availability, you must use the other tools.
2. Getting pricing for a list of item codes (get_pricing_tool)
3. Getting availability for a list of item codes (get_availability_tool)

If one tool is not able to provide the information you need, use the other tools.
ONLY OUTPUT INFORMATION THAT YOU HAVE RECEIVED FROM THE TOOLS.

When responding:
1. Always structure your responses clearly
2. Include relevant URLs, part numbers, and manufacturer numbers
3. Format prices and availability information consistently

Focus only on pool equipment, store details, and product
information for Heritage Pool Plus.

OUTPUT ---:
Return the product details in a structured format, based on the conversation history.
"""


def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    prompt = f"You have a pending request from the {pending_request.get('requesting_agent')} agent. Use the provided tools to provide a response. \
                      Use the information provided by  {pending_request.get('request_info')}  to respond to the user. Here is the general state of the conversation: {state}\
                      If a given number is ambigious, ask the user to clarify which number they are referring to."
    product_agent = create_react_agent(
        model=prebuilt_llm,
        state_modifier=system_message,
        tools=[
            get_product_details_tool,
            get_pricing_tool,
            get_availability_tool
        ],
        response_format=AgentResponse
    )
    response = product_agent.invoke({"messages": prompt})
    pending_request = None
    structured_response = response.get("structured_response")
    return Command(
        goto="supervisor",
        update={"messages": state["messages"] + [AIMessage(content=str(structured_response))], "pending_request": pending_request}
    )
    
def product_info_agent_node(state: State) -> Command[str]:
    try:
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
        product_agent = create_react_agent(
            model=prebuilt_llm,
            state_modifier=system_message,
            tools=[
                search_klevu_products_tool,
                search_azure_products_tool
            ],
            response_format=ProductInfo
)
        response = product_agent.invoke(state)
        structured_response = response.get("structured_response")
        return Command(goto="supervisor", update={"messages": state["messages"] + [AIMessage(content=str(structured_response))]})
    except Exception as e:
        logger.error(f"Error in product_agent_node: {str(e)}")
        raise