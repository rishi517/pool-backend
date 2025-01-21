from typing import Dict, Any, List, Optional
from langgraph.types import Command
from lib.types import prebuilt_llm, State, AgentRequest, BlogInfo
from firebase_functions import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.request_tools import search_blog_posts_tool

system_prompt = """You are the blog search agent for PartSelect's customer service system. Your role is to:
1. Search through PartSelect's blog posts for relevant information based on user queries
2. Extract and summarize helpful information from blog posts
3. Provide clear, concise responses with relevant blog content

You may not use any knowledge of PartSelect or external websites outside of the information provided in the conversation by either the user or the blog search results.

Your workflow:
1. Analyze the user's query to understand what information they're looking for
2. Use the search_blog_posts_tool to find relevant articles
3. Extract and summarize the most relevant information
4. If the query is unclear or too broad, request clarification from the user

Output must be structured exactly as:
{
    "search_query": "the search query used or needed",
    "found_articles": ["list", "of", "relevant", "articles"] or [],
    "info_needed": an AgentRequest object if you need more information from the user, otherwise null
}

An AgentRequest object is a JSON object with the following structure:
{
    "requesting_agent": "blog_agent",
    "target_agent": "human_interaction",
    "request_type": "clarify_query",
    "request_info": "specific information needed from the user"
}

Example Scenarios:
"How do I maintain my refrigerator?"
Steps:
    1) Use the search_blog_posts_tool to search for refrigerator maintenance articles
    2) Extract relevant information from the articles
    3) If articles are found, set found_articles to the list of articles
    4) If query is too broad, set info_needed to request more specific information

Focus only on Refrigerator and Dishwasher related information from the blog posts."""

blog_agent = create_react_agent(
    model=prebuilt_llm,
    state_modifier=system_prompt,
    tools=[search_blog_posts_tool],
    response_format=BlogInfo
)

def analyze_blog_query(state: State) -> BlogInfo:
    """Analyze the conversation to determine the search query and needed information."""
    try:
        analysis_messages = {"messages": state["messages"] + [
            HumanMessage(content="""Analyze the conversation and determine:
            1. What specific information the user is looking for
            2. If we need to ask for clarification
            Return this as a BlogInfo object.""")
        ]}
        
        response = blog_agent.invoke(analysis_messages)
        structured_response = response.get("structured_response")
        logger.debug(f"Blog query analysis: {structured_response}")
        return structured_response
        
    except Exception as e:
        logger.error(f"Error in analyze_blog_query: {str(e)}")
        raise

def handle_pending_request(state: State, pending_request: AgentRequest) -> Command[str]:
    try:
        prompt = f"You have a pending request from {pending_request.get('requesting_agent')}.\
                  Use this information to search the blog: {pending_request.get('request_info')}"
        response = blog_agent.invoke({"messages": prompt})
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
                "messages": state["messages"] + [AIMessage(content=str(response))],
                "pending_request": None
            }
        )
    except Exception as e:
        logger.error(f"Error in handle_pending_request: {str(e)}")
        raise

def blog_agent_node(state: State) -> Command[str]:
    try:
        logger.debug(f"State in blog_agent_node: {state}")
        
        if state.get("pending_request"):
            return handle_pending_request(state, state.get("pending_request"))
        
        # Analyze the query
        response = blog_agent.invoke(state)
        structured_response = response.get("structured_response")
        logger.debug(f"Response in blog_agent_node: {structured_response}")
        
        return Command(
            goto="supervisor",
            update={
                **state,
                "messages": state["messages"] + [AIMessage(content=str(structured_response))],
                "pending_request": structured_response.get("info_needed")
            }
        )
        
    except Exception as e:
        logger.error(f"Error in blog_agent_node: {str(e)}")
        raise 