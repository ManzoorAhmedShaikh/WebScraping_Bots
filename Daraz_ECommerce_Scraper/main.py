import os
import math
import time
import random

import curl_cffi.requests.session
import pandas as pd
from curl_cffi import requests

SEARCH_KEYWORD = "SEARCH KEYWORD" #Enter you search keyword here
ALL_RESULTS = False # Set (True) if you want all pages data, otherwise it will retrieve only first page data
EXPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"({SEARCH_KEYWORD})_Extracted_Data.csv")
URL = "https://www.daraz.pk/catalog/"
PARAMS = {
    "ajax": "true",
    "page": 1,
    "q": "search_keyword"
}
ITEMS_PER_PAGE = 40
MIN_DELAY = 3
MAX_DELAY = 5


def create_session():
    """
    Creates a fresh session with a real Chrome fingerprint.
    """
    print("create_session() Creating a new session")
    return requests.Session(
        impersonate="chrome120",
        timeout=10
    )

def data_extraction(data_to_extract : list[dict]):
    """
    A common method that will populate the data into the EXTRACTED_DATA list from the response
    :param data_to_extract: A list of dictionaries of data which needs to be populated in the finalized data variable EXTRACTED_DATA
    :return: None
    """

    print("data_extraction() Started!")
    for data in data_to_extract:
        extracted_data_structure = {
            "Product Name": data.get('name').strip(),
            "Product Description": data.get('description')[0].strip() if len(
                data.get('description')) >= 1 else "Not Available",
            "Price": float(data.get('price')),
            "Rating score": data.get('ratingScore') if data.get('ratingScore', "") != "" else "Not Available",
            "In Stock": "Yes" if data.get('inStock') == True else "No",
            "Total Sold": data.get('itemSoldCntShow').split()[0] if data.get(
                'itemSoldCntShow', "Not Available") != "Not Available" else "Not Available",
            "Seller": data.get("sellerName", "")
        }
        EXTRACTED_DATA.append(extracted_data_structure)
    print("data_extraction() Ended!")

def get_first_page_data(session : curl_cffi.requests.session.Session):
    """
    It will fetch the first result to get the total number of pages if return by the SEARCH_KEYWORD, otherwise, if it doesn't fetch
    anything, it will abort the whole operation of scrapping.
    :param session: The session from which we will send the request to Daraz.pk web pages.
    :return: total_pages_to_scrap (int): The total number of pages that are available to scrap.
    """

    print("get_first_page_data() Started!")
    total_pages_to_scrap = 0
    try:
        PARAMS.update({"q": SEARCH_KEYWORD})
        response = session.get(URL, params=PARAMS)

        if response.status_code == 200:
            page_data = response.json()
            total_pages_to_scrap = math.ceil(int(page_data.get('mainInfo', {}).get('totalResults')) / ITEMS_PER_PAGE)
            complete_data = page_data.get('mods', {}).get('listItems', {})

            if len(complete_data) != 0:
                data_extraction(data_to_extract = complete_data)
                time.sleep(random.randint(MIN_DELAY,MAX_DELAY))
                print("get_first_page_data() Retrieved the page: 1 data successfully.")
                print("get_first_page_data() Ended successfully.")

            else:
                print(f"get_first_page_data() Unable to find any data for the '{SEARCH_KEYWORD}' keyword, try search for something else.")
        else:
            print(f"get_first_page_data() Unable to send the request due to an error -> '{response.content}', aborting the data extraction!")
    except Exception as err:
        print(f"get_first_page_data() Ended with an error -> {err}")
    return total_pages_to_scrap

def search_and_extract(session : curl_cffi.requests.session.Session, actual_pages : int, max_pages : int = 2):
    """

    :param session: The session from which we will send the request to Daraz.pk web pages.
    :param actual_pages: The actual number of pages extracted from previous function get_first_page_data
    :param max_pages: The maximum pages to extract, by default they are 2 pages.
    :return: None
    """
    print("search_and_extract() Started")
    try:

        #All pages will be extracted if ALL_RESULTS is True, othersie only 2nd page extracted
        if ALL_RESULTS:
            print(f"search_and_extract() All pages: {actual_pages} will be scrapped")
            max_pages = actual_pages

        for page in range(2, max_pages + 1):
            PARAMS.update({"page": page})
            response = session.get(URL, params=PARAMS)

            if response.status_code == 200:
                complete_data = response.json().get('mods', {}).get('listItems', {})
                data_extraction(data_to_extract = complete_data)
                time.sleep(random.randint(MIN_DELAY,MAX_DELAY))
                print(f"search_and_extract() Retrieved the page: {page} data successfully.")

            else:
                print(f"search_and_extract() Unable to send the request due to an error -> '{response.content}', skipping and moving to next product!")

        print(f"search_and_extract() Ended successfully.")
    except Exception as err:
        print(f"search_and_extract() Ended with an error -> {err}")

def run():
    print("Scrapper Execution started!")

    global EXTRACTED_DATA
    EXTRACTED_DATA = []

    session = create_session()
    total_pages = get_first_page_data(session = session)
    if total_pages > 0:
        if total_pages > 1:
            search_and_extract(session = session, actual_pages = total_pages)

        df = pd.DataFrame(EXTRACTED_DATA)
        df.index = df.index + 1
        df.to_csv(EXPORT_PATH, index_label="S.No")

    session.close()
    print("Scrapper Execution Ended!")

if __name__ == "__main__":
    run()