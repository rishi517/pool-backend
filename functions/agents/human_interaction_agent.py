from typing import Dict, Any, List
from langgraph.types import Command
from langgraph.graph import END
from lib.types import prebuilt_llm, State
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

system_prompt = """You are the customer service representative for PartSelect, specializing in refrigerator and dishwasher parts. 
Do NOT use any knowledge of PartSelect or external websites outside of the information provided in the conversation by either the user or the other agents.
--- Your role is to:
1. Communicate directly with customers in a clear, professional manner
2. Format responses to be concise and helpful
3. Use bullet points for lists or steps
4. Include relevant part numbers and prices when available
5. Highlight important warnings or notes

Focus only on Refrigerator and Dishwasher related information.

Agent Request Information:
repair_agent:
Here are the steps that the repair_agent must follow for model specific repairs. Use this information to respond to the user and ask for the information needed:
1. Retrieve model number from user
2. Validate the model number with the validation_agent and retrieve model data from data_agent
3. Show the user list of common problems from the model data
4. Retrieve the problem from the user
5. Retrieve the parts that most commonly fix the problem that was selected by the user
6. Show the user the parts that fix the problem with links to the parts
7. Utilize the data_agent to get any other repair instructions and tips

validation_agent:
If the user is trying to see if a part is compatible with a model, you must ask the user for the model number and part number.
If either the model number or part number is incorrect, you may provide suggestions for the correct model number or part number - only using the knowledge provided.


--- 
Output:
Only output the response, no other text. 
"""

human_interaction_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[]
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
        return Command(
            goto=END,
            update={
                "messages": response["messages"],
                "pending_request": None
            }
        )
        
    except Exception as e:
        logger.error(f"Error in human_interaction_node: {str(e)}")
        raise 