from typing import Dict, Any, List
from langgraph.types import Command
from lib.types import AgentRequest, AgentResponse, prebuilt_llm, State, StoreList
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from tools.store_tools import search_store_locations_tool


system_message = """You are a the store search expert agent for Heritage Pool's customer service system. 

Minimize the number of tools you use.

Your capabilities include:
1. Searching for store locations using the search feature (search_store_locations_tool)
2. Getting store details for a specific store id (get_store_details_tool)
3. Getting store hours for a specific store id (get_store_hours_tool)

ONLY OUTPUT INFORMATION THAT YOU HAVE RECEIVED FROM THE TOOLS.


When responding:
1. Always structure your responses clearly


Focus only on store details for Heritage Pool Plus.

OUTPUT ---:
Return the store details in a structured format, based on the conversation history.
"""



def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    prompt = f"You have a pending request from the {pending_request.get('requesting_agent')} agent. Use the provided tools to provide a response. \
                      Use the information provided by  {pending_request.get('request_info')}  to respond to the user. Here is the general state of the conversation: {state}\
                      If a given number is ambigious, ask the user to clarify which number they are referring to."
    store_agent = create_react_agent(
        model=prebuilt_llm,
        state_modifier=system_message,
        tools=[
            search_store_locations_tool
        ],
        response_format=AgentResponse
    )
    response = store_agent.invoke({"messages": prompt})   
    pending_request = None
    structured_response = response.get("structured_response")
    return Command(
        goto="supervisor",
        update={"messages": state["messages"] + [AIMessage(content=str(structured_response))], "pending_request": pending_request}
    )
    
def store_search_agent_node(state: State) -> Command[str]:
    try:
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
        store_agent = create_react_agent(
            model=prebuilt_llm,
            state_modifier=system_message,
            tools=[
                search_store_locations_tool
            ],
            response_format=StoreList
        )
        response = store_agent.invoke(state)
        structured_response = response.get("structured_response")
        return Command(goto="supervisor", update={"messages": state["messages"] + [AIMessage(content=str(structured_response))]})
    except Exception as e:
        logger.error(f"Error in store_search_agent_node: {str(e)}")
        raise