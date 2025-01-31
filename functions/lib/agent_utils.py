from typing import Dict, Any, List, Optional, Callable
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

def convert_dict_to_langchain_messages(messages: List[Dict[str, str]]) -> List[BaseMessage]:
    """Convert dictionary messages to LangChain message format."""
    converted_messages = []
    for msg in messages:
        if isinstance(msg, (AIMessage, HumanMessage, SystemMessage)):
            converted_messages.append(msg)
        else:
            if msg["role"] == "system":
                converted_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                converted_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "user":
                converted_messages.append(HumanMessage(content=msg["content"]))
    return converted_messages


