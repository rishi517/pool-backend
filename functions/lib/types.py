from typing import Literal, Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from pydantic import Field
from typing_extensions import TypedDict
import os

prebuilt_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)
agents = Literal["human_interaction", "product_agent", "store_agent", "store_search_agent", "store_info_agent"]
# Define valid agent interactions
VALID_AGENT_REQUESTS = {
    "human_interaction": [],
    "product_search_agent": ["human_interaction"],
    "product_info_agent": ["product_search_agent", "store_search_agent", "store_info_agent", "human_interaction"],
    "store_search_agent": ["human_interaction"],
    "store_info_agent": ["store_search_agent", "product_search_agent", "product_info_agent", "human_interaction"]
}


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

class AgentStructuredResponse(TypedDict):
    child_agent_response: Optional[AgentResponse] = Field(default=None, description="The response from the child agent")
    pending_request: Optional[AgentRequest] = Field(default=None, description="The pending request from the child agent")
    
class State(TypedDict):
    messages: List[Message] = Field(..., description="The conversation messages")
    current_agent: str = Field(..., description="The currently active agent")
    pending_request: Optional[AgentRequest] = Field(default=None, description="Pending agent request")
    agent_scratchpad: Optional[str] = Field(default="", description="The scratchpad of the agent that made the request")
    output_image: Optional[str] = Field(default=None, description="The image to be displayed to the user, as a URL")

class Product(TypedDict):
    name: str = Field(..., description="The name of the product")
    part_number: Optional[str] = Field(default=None, description="The part number of the product")
    manufacturer_number: Optional[str] = Field(default=None, description="The model number of the product")
    price: Optional[str] = Field(default=None, description="The price of the product")
    image_url: Optional[str] = Field(default=None, description="The URL of the product image")
    additional_info: Optional[str] = Field(default=None, description="Additional information about the product")
    description: Optional[str] = Field(default=None, description="The description of the product")

class ProductList(AgentStructuredResponse):
    products: List[Product] = Field(default_factory=list, description="List of relevant products found")

class ProductInfo(AgentStructuredResponse):
    search_query: Optional[str] = Field(default=None, description="The search query provided by the user")
    found_products: List[Product] = Field(default_factory=list, description="List of relevant products found")
    suggested_response: Optional[str] = Field(default=None, description="A suggested response to the user, based on the search query")
    info_needed: Optional[AgentRequest] = Field(default=None, description="Set to None if all information is provided, otherwise set to the request needed")
    
class Store(TypedDict):
    name: str = Field(..., description="The name of the store")
    longitude: Optional[float] = Field(default=None, description="The longitude of the store")
    latitude: Optional[float] = Field(default=None, description="The latitude of the store")
    phone_number: Optional[str] = Field(default=None, description="The phone number of the store")
    website_url: Optional[str] = Field(default=None, description="The website URL of the store")

class StoreList(AgentStructuredResponse):
    found_stores: List[Store] = Field(default_factory=list, description="List of relevant stores found")

class StoreInfo(AgentStructuredResponse):
    search_query: Optional[str] = Field(default=None, description="The search query provided by the user")
    found_stores: List[Store] = Field(default_factory=list, description="List of relevant stores found")
    suggested_response: Optional[str] = Field(default=None, description="A suggested response to the user, based on the search query")
    info_needed: Optional[AgentRequest] = Field(default=None, description="Set to None if all information is provided, otherwise set to the request needed")
    
    
class FinalOutput(TypedDict):
    message: List[Message] = Field(..., description="The conversation messages")
    output_image: Optional[str] = Field(default=None, description="The image to be displayed to the user, as a URL")