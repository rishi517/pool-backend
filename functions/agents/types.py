from typing import Literal, Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from pydantic import Field
from typing_extensions import TypedDict
import os

prebuilt_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)
agents = Literal["human_interaction", "validation_agent", "repair_agent", "data_agent", "summary_agent"]
# Define valid agent interactions
VALID_AGENT_REQUESTS = {
    "human_interaction": [],
    "validation_agent": ["data_agent", "summary_agent", "human_interaction"],
    "repair_agent": ["validation_agent", "data_agent", "summary_agent", "human_interaction"],
    "data_agent": ["human_interaction"],
    "summary_agent": []
}

class ValidationInfo(TypedDict):
    is_valid_or_compatible: bool = Field(..., description="Whether the item is valid or compatible")
    found_item: Optional[str] = Field(..., description="The item that was found")
    item_suggestions: Optional[List[str]] = Field(..., description="A list of suggestions for the user to provide a part number or model number if the item was not found")


    
class MessageSummary(TypedDict):
    part_numbers: Optional[List[str]] = Field(..., description="A list of part numbers that have been mentioned")
    model_numbers: Optional[List[str]] = Field(..., description="A list of model numbers that have been mentioned")
    issues_reported: Optional[List[str]] = Field(..., description="A list of issues that have been reported")
    validated_info: Optional[List[str]] = Field(..., description="A list of information that has been validated")
    repair_suggestions: Optional[List[str]] = Field(..., description="A list of repair suggestions that have been made")
    pending_questions: Optional[List[str]] = Field(..., description="A list of questions that are still pending")
    current_state: Optional[str] = Field(..., description="The current state of the conversation")
    conversation_summary: Optional[str] = Field(..., description="A summary of the conversation so far")

class Message(TypedDict):
    role: Literal["system", "user", "assistant"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(..., description="The name of the agent that sent the message")

class AgentRequest(TypedDict):
    requesting_agent: agents = Field(..., description="The agent making the request")
    target_agent: agents = Field(..., description="The agent being requested")
    request_type: str = Field(..., description="The type of request being made")
    request_info: str = Field(..., description="Information for the target agent to process the request")

class AgentResponse(TypedDict):
    responding_agent: agents = Field(..., description="The agent providing the response")
    requesting_agent: agents = Field(..., description="The agent that made the request")
    response_data: Dict[str, Any] = Field(..., description="The response data")
    
class RepairInfo(TypedDict):
    provided_model_number: bool = Field(..., description="Whether the user has provided a model number")
    list_of_problems: List[str] = Field(..., description="A list of common problems that the user may be experiencing, only filled if the user has provided a model number")
    provided_problem: Optional[str] = Field(..., description="The problem that the user has provided, only filled if the user has provided a model number")
    list_of_parts: List[str] = Field(..., description="A list of parts that are needed to fix the problem, only filled if the user has provided a problem")
    info_needed: Optional[AgentRequest] = Field(..., description="Set to None if all information is provided, otherwise set to the request needed")
    
    

class State(TypedDict):
    messages: List[Message] = Field(..., description="The conversation messages")
    current_agent: str = Field(..., description="The currently active agent")
    pending_request: Optional[AgentRequest] = Field(default=None, description="Pending agent request")
    conversation_state: Dict[str, Any] = Field(default_factory=dict, description="Current state of the conversation")