from typing import List, Dict
from lib.types import prebuilt_llm

def summarize_conversation(messages: List[Dict[str, str]], keep_last: int = 3) -> List[Dict[str, str]]:
    """Summarize older messages while keeping recent ones intact."""
    if len(messages) <= keep_last:
        return messages
        
    # Keep the most recent messages as is
    recent_messages = messages[-keep_last:]
    older_messages = messages[:-keep_last]
    
    # Summarize older messages
    summary_prompt = """Summarize the key points from this conversation, focusing on:
    1. User's main problem or question
    2. Important part numbers or model numbers mentioned
    3. Key findings or solutions discussed
    Keep only the most relevant information."""
    
    summary = prebuilt_llm.invoke(
        f"{summary_prompt}\n\nConversation:\n" + 
        "\n".join([f"{m['role']}: {m['content']}" for m in older_messages])
    )
    
    # Create a summary message
    summary_message = {
        "role": "system",
        "content": f"Previous conversation summary: {summary}"
    }
    
    return [summary_message] + recent_messages 