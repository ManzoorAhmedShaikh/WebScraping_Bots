import time
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os

class Wish_Scraper:

    def __init__(self):
        """
        Wish.com Ecommerce Website Scraper based on the product you search.
        """

        options = Options()
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-cookies")
        self.driver = Chrome(options=options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)
        self.wait1 = WebDriverWait(self.driver,5)
        self.wait2 = WebDriverWait(self.driver,10)

        #2 Example Searches
        To_Search = "T-shirts"
        # To_Search = ["T-shirts",'sdasd',"Watches",'Clothes','Bag']

        self.Run(To_Search = To_Search)

    def Run(self, To_Search):
        """
        Main function to execute which deals with website loading, data scraping and exporting
        :param To_Search: (str) or (list) The product that we want to search for
        :return: None
        """

        print("*"*25 + str("Execution Started") + "*"*25)

        self.Load_Website()
        if isinstance(To_Search,list) and len(To_Search) >= 1:
            print("Run() :: Multiple Product Found!")
            for ToSearch in To_Search:
                Data_Dict = self.Search_and_Scrape(To_Search=ToSearch)
                self.Convert_and_Export(Dictionary = Data_Dict, FileName = ToSearch)

        else:
            Data_Dict = self.Search_and_Scrape(To_Search=To_Search)
            self.Convert_and_Export(Dictionary=Data_Dict, FileName=To_Search)

        print("*"*25 + str("Execution Ended") + "*"*25)

    def Load_Website(self):
        """
        It will load the website and deal with all the First occuring Popups and cookies
        :return: None -> Open the website
        """

        print("Load_Website() :: Started")

        Iframe_path = '//iframe[@title="TrustArc Cookie Consent Manager"]'
        Cookies_Accept_Close_Btn_path = '//div[@class="pdynamicbutton"]//a[1]'
        Email_PopUp_Close_Btn_path = "//div[starts-with(@class,'BaseModal__CloseButton')]"

        self.driver.get('https://www.wish.com/')
        iframe = self.driver.find_element(By.XPATH,Iframe_path)
        self.driver.switch_to.frame(iframe)

        Btn1 = self.wait1.until(EC.element_to_be_clickable((By.XPATH, Cookies_Accept_Close_Btn_path)))
        Btn1.click()
        time.sleep(1)
        Btn2 = self.wait1.until(EC.element_to_be_clickable((By.XPATH, Cookies_Accept_Close_Btn_path)))
        Btn2.click()
        time.sleep(1)

        try:
            PopUp_Close = self.wait1.until(EC.element_to_be_clickable((By.XPATH, Email_PopUp_Close_Btn_path)))
            PopUp_Close.click()
            print("Load_Website() :: Email PopUp found and closed")

        except Exception as er:
            print("Load_Website() :: No Email PopUp found")

        print("Load_Website() :: Ended")

    def Search_and_Scrape(self,To_Search = 'Watches for men'):
        """
        Search for the particular object pass in the param 'To_Search' and scrap all the Names, Prices and their Links of that product
        :param To_Search: (str) The product you want to search
        :return: (dict) A Dictionary of list that will be ready to convert into pandas Dataframe
        """

        print("Search_and_Scrape() :: Started")

        Scrapped_Data = {}
        Search_Field_path = "//input[starts-with(@class,'NavbarSearchBarV2')]"
        All_Items_Name_path = "//div[contains(@class,'ProductTileV2__NameWrapper')]/div"
        All_Items_Price_path = "//div[contains(@class,'FeedTile__PriceWrapper')]/div[1]"
        All_Items_Link_path = "//a[contains(@class,'FeedTile__Wrapper')]"

        self.driver.find_element(By.XPATH, Search_Field_path).send_keys(Keys.CONTROL + 'a')
        time.sleep(0.25)
        self.driver.find_element(By.XPATH, Search_Field_path).send_keys(Keys.DELETE)
        time.sleep(0.25)
        self.driver.find_element(By.XPATH, Search_Field_path).send_keys(To_Search)
        time.sleep(0.5)
        self.driver.find_element(By.XPATH, Search_Field_path).send_keys(Keys.ENTER)

        try:
            self.wait2.until(EC.element_to_be_clickable((By.XPATH, All_Items_Link_path)))
            if self.driver.find_element(By.XPATH,All_Items_Link_path).is_displayed() == True:
                print(f"Search_and_Scrape() :: Scraping Data for '{To_Search}'...")
                time.sleep(2)

                #Name sometime did not load on the web page
                Names = [o.text.strip() for o in self.driver.find_elements(By.XPATH,All_Items_Name_path)]
                if len(Names) == 0:
                    print(f"Search_and_Scrape() :: Name did not load on the website for '{To_Search}'")
                    return Scrapped_Data

                Prices = [o.text.strip() for o in self.driver.find_elements(By.XPATH,All_Items_Price_path)]
                Links = [o.get_attribute('href') for o in self.driver.find_elements(By.XPATH,All_Items_Link_path)]

                Scrapped_Data.update({
                    "Names": Names,
                    "Prices": Prices,
                    "Links": Links
                })
                print("Search_and_Scrape() :: Scrapped Successfully!")
                return Scrapped_Data

        except Exception as er:
            print(f"Search_and_Scrape() :: No Product found for the Search: '{To_Search}'")
            return Scrapped_Data

        print("Search_and_Scrape() :: Ended")

    def Convert_and_Export(self,Dictionary , FileName = 'Results'):
        """
        Convert the Dictionary to Dataframe and then export the data into the CSV file
        :param Dictionary: (dict) A Dictionary of list that will be ready to convert into pandas Dataframe
        :param FileName: (str) A Filename to be exported in CSV
        :return: None -> Export the files in Output Folder
        """

        print("Convert_and_Export() :: Started")
        try:
            if len(Dictionary) > 0:
                Dataframe = pd.DataFrame(Dictionary)
                Dataframe.index = Dataframe.index + 1

                print("Convert_and_Export() :: Processing_File...")
                os.makedirs('Output',exist_ok=True)
                Dataframe.to_csv(f'Output/{time.strftime("%H%M%S_") + str(FileName) + str("_File")}.csv')
                time.sleep(5)
            else:
                print(f"Convert_and_Export() :: The Dictionary is empty: {Dictionary} for the Product '{FileName}': Kindly verify if Search_and_Scrape() Function working fine")

        except Exception as er:
            print(f"Convert_and_Export() :: Unable to Create a file of FileName: '{FileName}' due to the ERROR: '{er}'")

        print("Convert_and_Export() :: Ended")

if __name__ == "__main__":
    Wish_Scraper()