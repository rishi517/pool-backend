from langchain.schema import HumanMessage, SystemMessage, AIMessage
from firebase_functions import logger
from dotenv import load_dotenv
from agents.supervisor_agent import build_supervisor_graph
from lib.types import State
import json
from lib.agent_utils import convert_dict_to_langchain_messages
load_dotenv()



def get_llm_response(messages):
    try:
        # Convert incoming messages to LangChain format
        logger.debug(f"Converting messages to langchain format: {messages}")
        try:
            langchain_messages = convert_dict_to_langchain_messages(messages)
            logger.debug("Messages converted successfully")
        except Exception as e:
            logger.error(f"Failed to convert messages: {str(e)}")
            raise

        try:
            state: State = {
                "messages": langchain_messages
            }
            logger.debug("State created successfully")
        except Exception as e:
            logger.error(f"Failed to create state: {str(e)}")
            raise

        try:
            logger.debug("Building supervisor graph")
            graph = build_supervisor_graph()
            logger.debug("Supervisor graph built successfully")
        except Exception as e:
            logger.error(f"Failed to build graph: {str(e)}")
            raise

        try:
            logger.debug("Running supervisor graph")
            response = graph.stream(state)
            logger.debug("Graph stream created successfully")
        except Exception as e:
            logger.error(f"Failed to create graph stream: {str(e)}")
            raise

        chunks = []
        output_message = "I'm sorry, I'm not sure what you're asking for. Please try again."
        
        output_image = None
        output = None
        try:
            logger.debug("Processing chunks")
            for chunk in response:
                logger.debug(f"Processing chunk: {json.dumps(chunk, default=str)}")
                chunks.append(chunk)
                for node_name, data in chunk.items():
                    logger.debug(f"Processing node {node_name}")
                    logger.debug(f"Data: {json.dumps(data, default=str)}")
                    if "messages" in data:
                        messages = data["messages"]
                        if messages and isinstance(messages[-1], AIMessage):
                            logger.debug(f"Messages: {messages[-1].content}")
                            output = messages[-1].content
                            
            if output:
                output = json.loads(output)
                output_message = output.get("message", "I'm sorry, I'm not sure what you're asking for. Please try again.")
                output_image = output.get("output_image", None)
                            
                logger.debug(f"New output: {output}")
                logger.debug(f"New output message: {output_message}")
        except Exception as e:
            logger.error(f"Failed to process chunks: {str(e)}")
            raise
        return output_message, output_image
        
    except Exception as e:
        logger.error(f"Error in get_llm_response: {str(e)}")
        raise Exception(f"Error processing query: {str(e)}")
