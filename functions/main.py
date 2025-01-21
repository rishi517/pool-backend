from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions import logger
from firebase_functions.options import CorsOptions

from langchain_client import get_llm_response

initialize_app()
__all__ = ["process_LLM_query"]

@https_fn.on_call(
    cors=CorsOptions(
        cors_origins=["*"],
        cors_methods=["GET", "POST", "OPTIONS"]
    ),
    timeout_sec=60
)
# input:
# {
#    "messages": an array of {"role": ..., "content"...} 
# }
# output:
# returns a string containing the LLM's response after processing the messages
def process_LLM_query(req: https_fn.Request) -> str:
    messages = req.data["messages"]    
    logger.debug(messages)
    response = get_llm_response(messages)
    logger.info(response)
    return response


