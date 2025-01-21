import requests
from firebase_functions import logger

from langchain.agents import Tool



headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": "phr_rule=organic; CountryCode=VT; _gcl_au=1.1.1430129604.1737052888; ai_user=xKCsLIUCW1j9OFCGcfg9pT|2025-01-16T18:41:27.881Z; GA_MrAppliance=dpouspm; _vwo_uuid_v2=D648F948F3B34B546132530DA6C80BAD2|a506281a3e4e88d8023490cf5c2f44be; _vwo_uuid=D648F948F3B34B546132530DA6C80BAD2; _vwo_ds=3%241737052887%3A71.10739035%3A%3A; _fbp=fb.1.1737052888923.601322635737039220; _pin_unauth=dWlkPVpEZGtaRFJtWWpNdFlXSTVNaTAwTXpSa0xUZzVZV0l0WkRaa1lqTmxZV00zTVRNeg; __idcontext=eyJjb29raWVJRCI6IjJyaXJsakdJcXNLYUI4M09pZ0lhbVFkV0hYVCIsImRldmljZUlEIjoiMnJpcmxqanZ2QnJ6ZkdiOWJKcnJTTWlOTXB5IiwiaXYiOiIiLCJ2IjoiIn0%3D; _hjSessionUser_1213522=eyJpZCI6ImJhMTU0YzM2LTMyYTItNTk2Yi1iN2YyLTFmMTJlODY0ZmMzOCIsImNyZWF0ZWQiOjE3MzcwNTI4ODkwNjcsImV4aXN0aW5nIjp0cnVlfQ==; _gid=GA1.2.986064234.1737145013; _vis_opt_exp_47_combi=3; FirstVisit=usvf; _vis_opt_exp_47_goal_5=1; _vis_opt_s=3%7C; _vis_opt_test_cookie=1; IR_gbd=partselect.com; clearRVDataOnLoad=Efmfufe; .AspNetCore.Antiforgery.Xh2vXOVYRfQ=CfDJ8MxFXhWWlKdLsXYEntchT1ugHGFxAp5MDjar0j4JhcXV02myL47r9gRcjW_UKgWLkP1txW8vVnOiD19YqyVKO1WF3_2DkXMz819klAQB-D8NrHCvKHbFWVp-7PCeZPIjEEaC99OvR3c18PvK7_SZwrQ; _vis_opt_exp_44_combi=2; _hjSession_1213522=eyJpZCI6ImU3ZjVhMDYzLTAzOWMtNDI5Zi1hMDkwLTU4YzA3NWM4MWFmZSIsImMiOjE3MzczMTMxOTQwNjQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; bounceClientVisit7449v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgO6kB0EAhgE4IoCmY9AxgmcwPYC2RASvQDNqASwDm9apQQdqAWgAKNOmURcQAGhDUYIUsQpKGTVu24aQwlAH1RHKwxQphHAHYwBlMA02WbEe-SOzm7QHl70AL5AA; GABRAND=Frigidaire; ASP.NET_SessionId=qtr5q3axxwxa4d5k1ai2mvwj; __utmc=154350649; acqData=%8C%33dbnqbjho%33%4B%33%39ejsfdu%3a%33%3D%33tpvsdf%33%4B%33%39ejsfdu%3a%33%3D%33nfejvn%33%4B%33%39opof%3a%33%3D%33dpoufou%33%4Bovmm%3D%33ufsn%33%4Bovmm%8E; __utmz=154350649.1737320138.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); PageViewCount=2; chref=/PartSearchResults.aspxds; SearchSession_LT=afb71724-3gg3-ba4a-2d51-61e2ec24gdbb; SearchSession_LT_Count=1; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Jan+19+2025+15%3A55%3A39+GMT-0500+(Eastern+Standard+Time)&version=202401.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CBG24%3A1%2CC0004%3A1%2CC0007%3A0&AwaitingReconsent=false; pscrtitc=0; _ga=GA1.2.180854216.1737052889; _ga_4NJ2YKSQY4=GS1.1.1737317868.13.1.1737320139.47.0.0; _uetsid=fe356f10d50f11ef91a43517e05ff4d0; _uetvid=7f8299c0d43911ef9fd6818507890c3b; IR_22088=1737320139127%7C0%7C1737320139127%7C%7C; __kla_id=eyJjaWQiOiJOREV4WlRBeE9ESXRaV1ZsTnkwME1qUmxMVGd4TkRJdE1qUXhNMkV5T1RZeU9HVTEiLCIkcmVmZXJyZXIiOnsidHMiOjE3MzcwNTI4ODksInZhbHVlIjoiaHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8iLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cucGFydHNlbGVjdC5jb20vIn0sIiRsYXN0X3JlZmVycmVyIjp7InRzIjoxNzM3MzIwMTM5LCJ2YWx1ZSI6Imh0dHBzOi8vd3d3LnBhcnRzZWxlY3QuY29tL25zZWFyY2hyZXN1bHQvP01vZGVsSUQ9V1I1NWRkWDEwMDI1Jm5vZnV6enk9MSIsImZpcnN0X3BhZ2UiOiJodHRwczovL3d3dy5wYXJ0c2VsZWN0LmNvbS9SZWZyaWdlcmF0b3ItUGFydHMuaHRtIn19; psclkfn=%8C%33JtMphhfeJo%33%4Bgbmtf%3D%33GjstuObnf%33%4B%33%33%8E; ai_session=i0HPwBYgWFL0VX/LZz+1Mt|1737318752447|1737320400397",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }

def request_page(url: str) -> str:
    """Request a page from the PartSelect website"""
    logger.info(f"Requesting page from {url}")
    response = requests.get(url, headers=headers, allow_redirects=True)
    logger.info(response.text)
    return response.text

request_page_tool = Tool(
        name="request_page",
        func=request_page,
        description="INFO: \
                    Request a page from the PartSelect website. \
                    --- \
                    Rules: \
                    input: url. Use this tool to get the HTML page for a specific URL on the PartSelect website. \
                    Do not run this tool on any other website.\
                    Only use this tool on URLs that are found in the output of another tool. \
                    This tool is useful if you are stuck, and find a URL in the output of another tool that you can use to get more information. \
                    Prioritize the other tools first, and only use this tool if no other tools are applicable."
)



def use_search_feature(search_term: str) -> str:
    """Use the search feature on the PartSelect website to get detailed information about a specific part or model"""
    logger.info(f"Getting HTML page for {search_term}")
    url = f"https://www.partselect.com/api/search/?searchterm={search_term}"
    response = request_page(url)
    logger.info(response)
    return response

use_search_feature_tool = Tool(
        name="use_search_feature",
        func=use_search_feature,
        description="INFO: \
                    Use the search feature on the PartSelect website to get detailed information about a specific part or model. \
                    --- \
                    Rules: \
                    input: search_term - the model id, part id, model name, or part name to search for. You can also search using a part description.\
                    Keep any non-id search terms as simple as possible (3 words or less). \
                    Analyze the output page to determine the best course of action, given the user's query. You may navigate to another page to get more information using the request_page tool."
)



def check_part_compatibility(model_and_part: str) -> str:
    """Check if a part exists in the PartSelect catalog by ID"""
    logger.info(f"Checking part compatibility for {model_and_part}")
    model_id, part_id = model_and_part.split("|")
    # remove any letters from the part number
    if len(part_id) > 2 and part_id[0:2] == "PS":
        part_id = part_id[2:]
    elif len(part_id) > 1 and part_id[0:1] == "W":
        part_id = part_id[1:]
    try:
        api_url = f"https://www.partselect.com/api/Part/PartCompatibilityCheck?modelnumber={model_id}&inventoryid={part_id}&partdescription=undefined"

        response = request_page(api_url)
        logger.info(response.json())
        
        return response.json()["compatabilityCheckResult"]
    except requests.RequestException as e:
        logger.error(f"Error checking part existence: {e}")
        return f"Error checking if part {id} exists"
    
check_part_compatibility_tool = Tool(
        name="check_part_compatibility",
        func=check_part_compatibility,
        description="INFO: \
                    Checks if a model number and part number are compatible. \
                    --- \
                    Rules: \
                    input: model_id|part_id. Do not run this tool if the user does not give you the specific model and/or part number. \
                    if you get an error, run this again with swapped model and part number."
)

def search_instant_repairman_models(model_number: str) -> str:
    """Search for models based on a model number"""
    logger.info(f"Searching for models with model number {model_number}")
    url = f"https://www.partselect.com/instant-repairman/?handler=SearchModels&ModelNum={model_number}"
    response = request_page(url)
    logger.info(response)
    return response

search_instant_repairman_models_tool = Tool(
        name="search_instant_repairman_models",
        func=search_instant_repairman_models,
        description="INFO: \
                    Search for models based on a model number. \
                    --- \
                    Rules: \
                    input: model_number. Do not run this tool if the user does not give you the specific model number.\
                    output: an HTML page in string format with a list of common problems for that model. \
                    The problem id and model master id are found in the output"
)


# GET INSTANT REPAIRMAN PARTS
def get_instant_repairman_parts(model_problem_id: str) -> str:
    """Get parts for a specific model and problem"""
    model_id, problem_id = model_problem_id.split("|")
    url = f"https://www.partselect.com/instant-repairman/?handler=GetpartsList&ModelMasterID={model_id}&ProblemID={problem_id}"
    response = request_page(url)
    logger.info(response)
    return response

get_instant_repairman_parts_tool = Tool(
        name="get_instant_repairman_parts",
        func=get_instant_repairman_parts,
        description="INFO: \
                    Get parts for a specific model and problem. \
                    --- \
                    Rules: \
                    input: model_master_id|problem_id. Do not run this tool if you do not have a valid model_master_id and problem_id.\
                    if you do not have a valid problem_id or model_master_id, run the search_instant_repairman_models tool first. \
                    both of these ids are found in the output of the search_instant_repairman_models tool. \
                    The model_master_id is likely different from the model_id provided by the user. ONLY use the model_master_id found in the \
                    output of the search_instant_repairman_models tool.\
                    output: an HTML page in string format with a list of parts for that model and problem."
)


def search_blog_posts(search_term: str) -> str:
    """Search for blog posts on the PartSelect website"""
    logger.info(f"Searching for blog posts with search term {search_term}")
    search_term = search_term.replace(" ", "%20")
    url = f"https://www.partselect.com/content/blog/search/{search_term}/"
    response = request_page(url)
    logger.info(response)
    return response

search_blog_posts_tool = Tool(
        name="search_blog_posts",
        func=search_blog_posts,
        description="INFO: \
                    Search for blog posts on the PartSelect website. \
                    --- \
                    Rules: \
                    input: search_term. Keep your search term simple, and do not include any non-search terms.\
                    example: 'dishwasher repair' or 'refrigerator repair' or 'dishwasher door repair' or 'refrigerator door repair'.\
                    limit your search to dishwasher or refrigerator repair. \
                    output: an HTML page in string format with a list of blog posts for that search term."
                    )


def general_dishwasher_repair_tips() -> str:
    """Get general dishwasher repair tips"""
    logger.info(f"Getting general dishwasher repair tips")
    url = f"https://https://www.partselect.com/Repair/Dishwasher/"
    response = request_page(url)
    logger.info(response)
    return response

general_dishwasher_repair_tips_tool = Tool(
        name="general_dishwasher_repair_tips",
        func=general_dishwasher_repair_tips,
        description="INFO: \
                    Get general dishwasher repair tips. This is a general guide, and may not be specific to the user's problem."
)

def general_refrigerator_repair_tips() -> str:
    """Get general refrigerator repair tips"""
    logger.info(f"Getting general refrigerator repair tips")
    url = f"https://https://www.partselect.com/Repair/Refrigerator/"
    response = request_page(url)
    logger.info(response)
    return response

general_refrigerator_repair_tips_tool = Tool(
        name="general_refrigerator_repair_tips",
        func=general_refrigerator_repair_tips,
        description="INFO: \
                    Get general refrigerator repair tips. This is a general guide, and may not be specific to the user's problem."
)