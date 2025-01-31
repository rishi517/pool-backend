import re
from typing import List
import requests
from firebase_functions import logger

from langchain.agents import Tool

def search_klevu_products(term: str, page_size: int = 5, page: int = 1) -> str:
    """Search Klevu for products that match the search term"""
    logger.info(f"Searching Klevu for {term}")
    term = term.replace(" ", "%20")
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/search?term={term}&page_size={page_size}&page={page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Klevu search response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Klevu: {e}")
        return str(e)

search_klevu_products_tool = Tool(
    name="search_klevu_products",
    func=search_klevu_products,
    description="Search for products using the Klevu search engine. Returns part id and part_number for each product."
)

def search_azure_products(term: str, limit: int = 3) -> str:
    """Search Azure for products that match the search term"""
    logger.info(f"Searching Azure for {term}")
    term = term.replace(" ", "%20")
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/products/search?query={term}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Azure search response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Azure: {e}")
        return str(e)

search_azure_products_tool = Tool(
    name="search_azure_products",
    func=search_azure_products,
    description="Search for products using the Azure search engine. \
        Returns:\
        product_name, description, brand, part_number, manufacturer_id, heritage_link, image_url, relevance_score"
)


def get_product_details(part_number: str) -> str:
    """Get the details of a product using the PartSelect API"""
    logger.info(f"Getting details for {part_number}")
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/products/{part_number.upper()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Product details response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting product details: {e}")
        return str(e)

get_product_details_tool = Tool(
    name="get_product_details",
    func=get_product_details,
    description="Get specific information about a specific product IT DOES NOT INCLUDE PRICING OR AVAILABILITY. \
        Returns:\
        product_name, description, brand, part_number, manufacturer_id, heritage_link, image_url")


def get_pricing(item_codes: List[str]):
    """Get pricing for a list of item codes"""
    logger.info(f"Getting pricing for {item_codes}")
    url = f"https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/pricing"
    if type(item_codes) == str:
        item_codes = [item_codes]
    request_body = {
        "items": [{"item_code": item_code.upper(), "unit": "EA"} for item_code in item_codes]
    }
    try:
        logger.info(f"Request body: {request_body}")
        response = requests.post(url, json=request_body)
        response.raise_for_status()
        logger.info(f"Pricing response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting pricing: {e}")
        return str(e)

get_pricing_tool = Tool(
    name="get_pricing",
    func=get_pricing,
    description="Get pricing for a list of item codes. \
        Returns:\
        item_code, description, price, available_quantity, in_stock, unit"
)

def get_availability(item_codes: List[str]):
    """Get availability for a list of item codes"""
    logger.info(f"Getting availability for {item_codes}")
    try:
        response = get_pricing(item_codes)
        availability = [item["in_stock"] for item in response]
        quantity = [item["available_quantity"] for item in response]
        logger.info(f"Availability: {availability}, Quantity: {quantity}")
        ret = {
            "items": [{"item_code": item_code, "available_quantity": quantity, "in_stock": availability} for item_code, availability, quantity in zip(item_codes, availability, quantity)]
        }
        return ret
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        return str(e)

get_availability_tool = Tool(
    name="get_availability",
    func=get_availability,
    description="Get availability for a list of item codes. \
        Returns:\
        a list of item codes and their availability and quantity"
)


