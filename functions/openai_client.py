import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from firebase_functions import logger

OPENAI_API_KEY = os.environ.get("OPENAI_KEY")

if not OPENAI_API_KEY:
    # Possibly raise an error or fallback to local dev .env
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

assistant = client.beta.assistants.retrieve("asst_wDM5dV4Hg6CqwGDZHMGT9hMb")



def get_openai_completion(messages, functions=None, function_call="auto"):
    """
    Wrapper to call the OpenAI ChatCompletion endpoint.
    If you want to use function calling, pass in functions + function_call.
    """
    try:
        stream = client.beta.threads.create_and_run( assistant_id=assistant.id, thread={"messages": messages}, stream=True)
        
        for event in stream:
            if event.data.object == "thread.message" and event.data.status == "completed":
                return event.data.content[-1].text.value
        raise Exception("No message found")        


        
    except Exception as e:
        logger.error(str(e))
        return {"error": str(e)}

