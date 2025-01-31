import os
from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions import logger
from firebase_functions.options import CorsOptions
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from langchain_client import get_llm_response

initialize_app()
__all__ = ["whatsapp_webhook"]

rishi_phone_number = os.getenv("RISHI_PHONE_NUMBER")
def get_message_history(user_input):
    logger.info("Getting message history")
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    messages = []
    for message in twilio_client.messages.list():
        if message.from_ == rishi_phone_number:
            role = "user"
        else:
            role = "assistant"
        messages.append({"role": role, "content": message.body})
    return messages
def clear_message_history():
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    twilio_client.messages.delete()

@https_fn.on_request(
    timeout_sec=60
)
def whatsapp_webhook(request):
    logger.info("Whatsapp webhook called")
    logger.info(request.values)
    user_input = request.values.get('Body', "").lower()
    messages = get_message_history(user_input)
    logger.info(messages)
    
    logger.info(user_input)
    response = MessagingResponse()
    
    # handle conversations
    if user_input == "/clear":
        clear_message_history()
        response.message("Cleared messages")
        return str(response)
    
    llm_response = get_llm_response(messages + [{"role": "user", "content": user_input}])
    response.message(llm_response)
    
    logger.info(str(response))
    # need to return response 
    return str(response)




