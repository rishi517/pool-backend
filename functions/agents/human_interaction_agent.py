from typing import Dict, Any, List
from langgraph.types import Command
from langgraph.graph import END
from lib.types import FinalOutput, prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

system_prompt = """You are the customer service representative for Heritage Pool Plus, specializing in pool equipment, both specific and general questions. 
Do NOT use any knowledge of Heritage Pool Plus or external websites outside of the information provided in the conversation by either the user or the other agents.
--- Your role is to:
1. Communicate directly with customers in a clear, professional manner
2. Format responses to be concise and helpful
3. Use bullet points for lists or steps
4. Include relevant part numbers and prices when available
5. Highlight important warnings or notes
6. Summarize search results for the user


Focus only on pool equipment, store details, and product
information for Heritage Pool Plus.

You have the ability to display images to the user. If you have an image to display, set the output_image field in the state to the image URL.

You will return a structured response to the user.

{
    "message": "The message to the user",
    "output_image": "The image to display to the user, as a URL" (optional)
}

DO NOT MAKE UP ANY INFORMATION. Your job is to take all the previous responses, and reason about them to provide a helpful response to the user's request

Based on the conversation history and the user's most recent message, structure your response in a way that is helpful to the user.
When possible, put available IDs in the response, so that subsequent serverless functions can retrieve the information.

--- 
Output:
Only output the response to the user, no other text. 
"""

human_interaction_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[],
    response_format=FinalOutput
)


def human_interaction_node(state: State) -> Command[str]:
    try:
        logger.debug(f"State in human_interaction_node: {state}")
        

        
        # Generate response
        if state.get("pending_request"):
            info_needed = state.get("pending_request").get("request_info")
            response = human_interaction_agent.invoke(f"Other agents are requesting information about: {info_needed}. Use this state to respond to the user and ask for the information needed.")
        else:
            response = human_interaction_agent.invoke(state)
            
        logger.debug(f"Response in human_interaction_node: {response}")
        # Add our response to the messages, keeping only essential fields
        structured_response = response.get("structured_response")
        return Command(
            goto=END,
            update={
                "messages": response["messages"],
                "pending_request": None,
                "output_image": structured_response.get("output_image")
            }
        )
        
    except Exception as e:
        logger.error(f"Error in human_interaction_node: {str(e)}")
        raise 