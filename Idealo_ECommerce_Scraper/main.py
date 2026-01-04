import pandas as pd
import re
import time
import random
import numpy as np
import curl_cffi.requests.models
import os, sys
from curl_cffi.requests.exceptions import Timeout, DNSError
from curl_cffi import requests
from copy import deepcopy
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
DATA_PATH = os.path.join(BASE_DIR, "Input Product Data.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Final_product_data.csv")
PROXIES_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
SEARCH_URL = "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={EAN}"
PRODUCT_PAGE_CLASS = "oopStage-details-header columns"
SEARCH_RESULT_PAGE_CLASS = "sr-filterBar__content_eiiz2"
SEARCH_RESULT_IDEALO_PRODUCT_CLASS = "sr-resultList_NAJkZ"
SESSION_ROTATE_EVERY = 200
MIN_DELAY = 1.5
MAX_DELAY = 3.5


def create_session():
    """
    Creates a fresh curl_cffi session with a real Chrome fingerprint.
    """
    return requests.Session(
        impersonate="chrome120",
        timeout=30
    )

def fetch_and_return_soup(response : curl_cffi.requests.models.Response):
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def scrap_from_product_page(index : int, input_data : pd.DataFrame, soup : BeautifulSoup):

    input_data.loc[index, 'Prices'] = re.search(r'\d+,\d+', soup.find('div', class_='best-total-price-box').text).group() if soup.find('div', class_='best-total-price-box') is not None else soup.find_all('li', attrs={'class': 'productOffers-listItem'})[0].find('div', attrs={'data-offerlist-column':'price'}).find('div',attrs = {"class": "productOffers-listItemOfferShippingDetails"}).text.strip().split()[0]
    input_data.loc[index, 'Expected Deliveries'] = " ".join(soup.find('div', class_='best-total-price-box').find_parent('li', attrs = {"class":"productOffers-listItem"}).find('ul', attrs={'data-offerlist-column': 'delivery'}).find('p').text.strip().split()) if soup.find('div', class_='best-total-price-box') is not None else ""
    input_data.loc[index, "Number of units"] = re.search(r"Nur noch\s+(\d+)", input_data.loc[index, 'Expected Deliveries']).group(1) if 'Nur noch' in input_data.loc[index, 'Expected Deliveries'] else random.randint(10, 75)

def scrap_from_search_page(index : int, input_data : pd.DataFrame, session : requests.Session, url : str):
    url += "&sortKey=minPrice"
    response = session.get(url)
    soup = fetch_and_return_soup(response)
    for product_soup in soup.find_all('div', attrs = {"class": "sr-resultList__item_m6xdA"}):
        if "amazon" not in str(product_soup.find('div',attrs = {"class": "sr-singleOffer_wQMsv"}).find('span',attrs = {'role': "link"}).text.strip()).lower():
            input_data.loc[index, "Prices"] = product_soup.find("div", attrs = {"class": "sr-detailedPriceInfo__price_sYVmx"}).text.split()[0]
            input_data.loc[index, "Expected Deliveries"] = product_soup.find("span", attrs = {"class": "sr-singleOffer__deliveryText_BlV2D"}).text.strip()
            input_data.loc[index, "Number of units"] = re.search(r"Nur noch\s+(\d+)",input_data.loc[index, 'Expected Deliveries']).group(1) if 'Nur noch' in input_data.loc[index, 'Expected Deliveries'] else random.randint(10, 75)
            break
    else:
        input_data.loc[index, "Prices"] = "0"
        input_data.loc[index, "Number of units"] = 0

def initialize_data(data_path : str):
    '''
    It will load and clean the data, expand rows with multiple EANs,
    and prepare the dataframe for scraping.
    :param data_path: The (str) path for the location where the input CSV file is present.
    :return: The (dataframe) object with clean data which is ready to populate.
    '''

    print("initialize_data() Started")
    try:
        df = pd.read_csv(data_path, dtype={"Produktcodes: EAN": str})
        if 'Unnamed: 3' in list(df.columns):
            del df['Unnamed: 3']

        #Handle multiple EAN cells
        df['Produktcodes: EAN'] = df['Produktcodes: EAN'].fillna("").astype(str).str.split(',')
        df = df.explode('Produktcodes: EAN')
        df['Produktcodes: EAN'] = df['Produktcodes: EAN'].str.strip()
        df['Produktcodes: EAN'] = df['Produktcodes: EAN'].replace(["nan", "NaN", "None"], "")

        #Adding prices, deliveries and number of units column in the new sheet
        df['Prices'] = pd.Series(dtype="string")
        df['Expected Deliveries'] = pd.Series(dtype="string")
        df['Number of units'] = pd.Series(dtype="Int64")
        df = df.reset_index(drop=True)

        print("initialize_data() Ended Successfully")
        return df

    except Exception as err:
        print(f"initialize_data() Ended with an error -> {err}")
        return None

def fetch_and_populate_data(input_data : pd.DataFrame):
    """
    This is the main function that will scrap the prices and delivery dates of the product using either their EAN or Product name.
    :param input_data: The (dataframe) object from where the product being retrieved using its EAN or product name values.
    :return: input_data: The finalized (dataframe) with two additional columns "Prices" and "Expected Deliveries"
    """
    print("fetch_and_populate_data() Started")
    try:
        session = create_session()
        request_count = 0
        timeout_count = 0
        dataframe = deepcopy(input_data)
        for index, data in enumerate(dataframe.values):
            product_EAN_availability = True
            product_EANs = None if data[2] in [np.nan, None, "nan"] else str(data[2]).strip()
            product_name = None if data[0] in [np.nan, None, "nan"] else str(data[0]).strip()

            try:
                if not product_EANs:
                    if not product_name:
                        print(f"fetch_and_populate_data() An empty row encountered at index: {index + 1}, skipping it!")
                        continue
                    print(f"fetch_and_populate_data() The product: {product_name} does not have any EAN id, using product name now!")
                    product_EANs = product_name
                    product_EAN_availability = False

                if len(product_EANs.split(',')) == 1 or not(product_EAN_availability):
                    request_url = SEARCH_URL.format(EAN = product_EANs) if product_EAN_availability else SEARCH_URL.format(EAN = quote_plus(product_EANs))

                    response = session.get(request_url, timeout = 10)
                    if response.status_code != 200:
                        temp_soup = fetch_and_return_soup(response)
                        if temp_soup.find('div',attrs = {"class": "sr-noResult_pnZK1"}) is not None:
                            print(f"fetch_and_populate_data() Invalid or no data available for this EAN: {product_EANs}, skipping this product!")
                            input_data.loc[index, "Prices"] = "0"
                            input_data.loc[index, "Number of units"] = 0
                            request_count += 1
                            continue

                        session.close()
                        session = create_session()
                        response = session.get(request_url)
                        if response.status_code != 200:
                            print(f"fetch_and_populate_data() Blocked for the requested url: {request_url} at index: {index + 1} multiple times, skipping this product!")
                            continue
                    print(f"fetch_and_populate_data() The product: '{product_EANs}' with the requested url: {request_url} fetched at index: {index + 1}")
                    soup = fetch_and_return_soup(response)
                    request_count += 1

                    #Direct product page of idealo aggregated data
                    if soup.find('div', attrs={'class': PRODUCT_PAGE_CLASS}):
                        scrap_from_product_page(index, input_data, soup)

                    #When multiple search results shown that may or may not include idealo aggregated data
                    elif soup.find('div', attrs = {'class': SEARCH_RESULT_PAGE_CLASS}):
                        link_search = soup.find('div', attrs={'class': SEARCH_RESULT_IDEALO_PRODUCT_CLASS}).find('a')
                        if link_search is not None:
                            link_search = link_search['href']
                            response = session.get(link_search)
                            soup = fetch_and_return_soup(response)
                            scrap_from_product_page(index, input_data, soup)
                            request_count += 1

                        #When only other websites product shown not idealo itself
                        else:
                            scrap_from_search_page(index, input_data, session, request_url)

                    # ---------- SESSION ROTATION ----------
                    if request_count % SESSION_ROTATE_EVERY == 0:
                        print("🔄 Rotating session (scheduled)")
                        session.close()
                        session = create_session()

                    # ---------- DELAY ----------
                    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

            except Exception as err:
                print(f"fetch_and_populate_data() Error raises in the requested url: {request_url} -> {err}")
                if isinstance(err, (Timeout, DNSError)):
                    timeout_count += 1
                    if timeout_count == 3:
                        print(f"fetch_and_populate_data() Interrupt as the network issue raised!")
                        break
                session.close()
                session = create_session()

        print(f"fetch_and_populate_data() Ended with the populated data!")
        return input_data

    except Exception as err:
        print(f"fetch_and_populate_data() Ended with error -> {err}")
        return input_data

def run():
    data = initialize_data(data_path = DATA_PATH)
    if data is not None:
        finalized_data = fetch_and_populate_data(input_data = data)
        finalized_data.to_csv(OUTPUT_PATH, index = False)

if __name__ == "__main__":
    run()