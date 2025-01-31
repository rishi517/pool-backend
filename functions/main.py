import os
import time
from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions import logger
from firebase_functions.options import CorsOptions
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from langchain_client import get_llm_response

initialize_app()
__all__ = ["whatsapp_webhook"]
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

rishi_phone_number = os.getenv("RISHI_PHONE_NUMBER")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
def get_message_history():
    logger.info("Getting message history")
    
    messages = []
    for message in twilio_client.messages.list():
        if message.from_ == rishi_phone_number:
            role = "user"
        else:
            role = "assistant"
        messages.append({"role": role, "content": message.body})
    return messages
def clear_message_history():
    for message in twilio_client.messages.list():
        logger.info(message.status, message.body)
        if message.status != "receiving":
            message.delete()


@https_fn.on_request(
    timeout_sec=600
)
def whatsapp_webhook(request):
    logger.info("Whatsapp webhook called")
    logger.info(request.values)
    user_input = request.values.get('Body', "")
    
    
    logger.info(user_input)
    
    # start of new conversation
    if user_input == "/clear":
        clear_message_history()
        twilio_client.messages.create(
            to=rishi_phone_number,
            from_=twilio_phone_number,
            body="Cleared messages"
        )
        
    else:
        messages = get_message_history()
        logger.info(messages)
    
        llm_response, output_image = get_llm_response(messages + [{"role": "user", "content": user_input}])
        logger.info(llm_response, output_image)
        if output_image:
            twilio_client.messages.create(
                to=rishi_phone_number,
                from_=twilio_phone_number,
                body=llm_response,
                media_url=output_image
            )
        else:
            twilio_client.messages.create(
                to=rishi_phone_number,
                from_=twilio_phone_number,
                body=llm_response
            )
            
            
        logger.info(f"PRINTING FINAL OUTPUT")
        logger.info(llm_response)

    time.sleep(15)
    return ""
   
    




