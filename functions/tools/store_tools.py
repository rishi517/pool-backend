import re
from typing import List
import requests
from firebase_functions import logger

from langchain.agents import Tool




def search_store_locations(latitude: float, longitude: float, radius: int = 50, page_size: int = 10, page: int = 1) -> str:
    """Search for store locations that match the search term"""
    logger.info(f"Searching for store locations that match {latitude}, {longitude}, {radius}, {page_size}, {page}")
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/stores/search?latitude={latitude}&longitude={longitude}&radius={radius}&page_size={page_size}&page={page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Store locations search response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching store locations: {e}")
        return str(e)

search_store_locations_tool = Tool(
    name="search_store_locations",
    func=search_store_locations,
    description="Search for store locations that match the input latitude, longitude, radius, page_size, and page \
        Returns a list of id, name, location, address, contact, hours"
)


def get_store_details(store_id: str) -> str:
    """Get the details of a store"""
    logger.info(f"Getting details of store {store_id}")
    store_id = store_id.upper()
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/stores/{store_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Store details response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting store details: {e}")
        return str(e)

get_store_details_tool = Tool(
    name="get_store_details",
    func=get_store_details,
    description="Get the details of a store \
        returns id, name, location (latitude, longitude), address, contact"
)


def get_store_hours(store_id: str) -> str:
    """Get the hours of a store"""
    logger.info(f"Getting hours of store {store_id}")
    try:
        store_details = get_store_details(store_id)
        store_hours = search_store_locations(store_details["location"]["latitude"], store_details["location"]["longitude"], 1, 1, 1)["stores"][0]["hours"]
        return {"hours": store_hours}
    except Exception as e:
        logger.error(f"Error getting store hours: {e}")
        return str(e)

get_store_hours_tool = Tool(
    name="get_store_hours",
    func=get_store_hours,
    description="Get the hours of a store \
        returns hours"
)
