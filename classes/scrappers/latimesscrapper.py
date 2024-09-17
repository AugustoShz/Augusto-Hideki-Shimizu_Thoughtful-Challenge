import re
from robocorp import log
from html import unescape
from classes.News import News
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from dateutil.relativedelta import relativedelta
from classes.NoNewsException import NoNewsException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LaTimesScrapper:


    def __init__(self, query="", news_topics=[], 
                 news_types=[], months_count=0):

        self.query = query
        self.page_count = 0
        self.result_count = 0
        self.page_count_total = 0
        self.news_types_UUID = []
        self.news_topics_UUID = []
        self.news_types = news_types
        self.news_topics = news_topics
        self.months_count = months_count
        self.base_uri = "https://www.latimes.com/search?s=1"
        
        self.max_timestamp = datetime.today()
        self.max_timestamp = self.max_timestamp.replace(
            day=1,
            hour=0,
            minute=0,
            second=0, 
            microsecond=0
        )
        if months_count > 1:
            self.max_timestamp = self.max_timestamp - relativedelta(months = months_count - 1)

        self.max_timestamp = self.max_timestamp.timestamp()
        
        log.debug("", { 
            "event": "DEBUG_LATIMES_SCRAPER_INITIALIZE",
            "uri": self.base_uri,
            "query": self.query,
            "news_topics": self.news_topics,
            "news_types": self.news_types,
            "months_count": self.months_count,
            "page_count": self.page_count,
            "page_count_total": self.page_count_total,
            "result_count": self.result_count,
            "news_topics_UUID": self.news_topics_UUID,
            "news_types_UUID": self.news_types_UUID,
            "max_timestamp": self.max_timestamp
        })

    def get_news(self):

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        news_formated = []
        with webdriver.Chrome(options=chrome_options) as driver:
            try:
                driver.implicitly_wait(10)
                driver.set_window_size(1024, 768)
                
                # 1. CONVERTING TOPICS AND TYPES NAMES TO CORRESPONDING UUID
                driver.get(self.build_URI())

                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-results-module-main"))
                )

                try:
                    driver.find_element(by=By.CLASS_NAME, value="search-results-module-no-results")
                    raise NoNewsException
                except:
                    log.debug("", {"event":"DEBUG_LATIMES_RESULTS_EXISTS"})

                if(len(self.news_topics)):
                    topics = driver.find_elements(by=By.NAME, value="f0")
                    for topic in topics:
                        parent = topic.find_element(by=By.XPATH, value="..")
                        span = parent.find_element(by=By.TAG_NAME, value="span")
                        topic_text = unescape(span.get_attribute("innerHTML")).strip().lower()
                        if topic_text in self.news_topics:
                            self.news_topics_UUID.append(topic.get_attribute("value"))

                    log.debug("", {
                        "event": "DEBUG_LATIMES_TOPICS_UUID",
                        "topics": self.news_topics,
                        "topics_uuid": self.news_topics_UUID
                    })

                if(len(self.news_types)):
                    types = driver.find_elements(by=By.NAME, value="f1")
                    for type in types:
                        parent = type.find_element(by=By.XPATH, value="..")
                        span = parent.find_element(by=By.TAG_NAME, value="span")
                        type_text = unescape(span.get_attribute("innerHTML")).strip().lower()
                        if type_text in self.news_types:
                            self.news_types_UUID.append(type.get_attribute("value"))

                    log.debug("", {
                        "event": "DEBUG_LATIMES_TYPES_UUID",
                        "types": self.news_types,
                        "types_uuid": self.news_types_UUID
                    })

                # 2. GETTING AMOUNT OF PAGES AND RESULTS
                driver.get(self.build_URI())
                
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-results-module-main"))
                )

                page_count_raw = driver.find_element(by=By.XPATH, value="/html/body/div[2]/ps-search-results-module/form/div[2]/ps-search-filters/div/main/div[2]/div[2]")
                page_count_text = page_count_raw.get_attribute("innerHTML")
                self.page_count_total = int(re.sub(",", "", re.sub(r"1 of ((?:\d+,?)+)", r"\1", page_count_text)))
                self.page_count = min(10, self.page_count_total)

                log.debug("", {
                    "event": "DEBUG_LATIMES_PAGE_COUNT",
                    "total_pages": self.page_count_total,
                    "page_count": self.page_count
                })

                result_count_raw = driver.find_element(by=By.CLASS_NAME, value="search-results-module-count-desktop")
                result_count_text = result_count_raw.get_attribute("innerHTML")
                self.result_count = int(re.sub(r",", "", re.search(r"(\d+,?)+", result_count_text)[0]))

                log.debug("", {
                    "event": "DEBUG_LATIMES_RESULT_COUNT",
                    "result_count": self.result_count
                })

                # 3. ITERATING PAGES
                last_news_timestamp = datetime.today().timestamp()
                for page in range(self.page_count):
                    driver.get(self.build_URI(page + 1))

                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "search-results-module-main"))
                    )

                    news_list = driver.find_elements(by=By.CSS_SELECTOR, value=".search-results-module-results-menu > li")

                    # 4. CHECKING IF DATE SURPASSES MONTHS DEFINED IN WorkItem 
                    if(self.max_timestamp > last_news_timestamp):
                        break

                    # 5. ITERATING RESULTS
                    for news_element in news_list:
                        news_without_image = False

                        #6. CHECK IF RESULT HAS IMAGE (IT CHANGES THE XPATH OF THE OTHER ATRIBUTES)
                        try:
                            news_image_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div[1]/a/picture/img")
                        except:
                            news_without_image=True
                            log.debug("", {"event": "DEBUG_LATIMES_NEWS_WITHOUT_IMAGE"})
                        
                        #7. GETTING RESULT ELEMENTS (TITLE, DATE, DESCRIPTION AND IMAGE IF AVAILABLE)
                        if(news_without_image):
                            news_title_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div/div/h3/a")
                            news_timestamp_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div/p[2]")
                            news_description_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div/p[1]")
                            news_image = None
                        else:
                            news_title_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div[2]/div/h3/a")
                            news_timestamp_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div[2]/p[2]")
                            news_description_element = news_element.find_element(by=By.XPATH, value="./ps-promo/div/div[2]/p[1]")
                            news_image = news_image_element.get_attribute("src")

                        news_title = news_title_element.get_attribute("innerHTML")
                        news_description = news_description_element.get_attribute("innerHTML")
                        news_timestamp = int(news_timestamp_element.get_attribute("data-timestamp"))/1000
                        last_news_timestamp = news_timestamp

                        log.debug("", {
                            "event": "DEBUG_LATIMES_NEWS_DATA",
                            "news_title": news_title,
                            "news_description": news_description,
                            "news_timestamp": news_timestamp,
                            "news_image": news_image
                        })

                        if(self.max_timestamp > news_timestamp):
                            break

                        #8. FORMATTING NEWS
                        news_object = News(
                            news_title, news_timestamp, news_description,
                            news_image, self.query
                        )

                        news_formated.append(news_object)

                        log.debug("", {
                            "event": "DEBUG_LATIMES_NEWS_FORMATED_DATA",
                            **news_object.to_dict()
                        })
            except NoNewsException:
                log.debug("", {"event":"DEBUG_LATIMES_NO_RESULTS"})
            except Exception as x:
                log.critical("Scraper ended with errors", {
                    "event": "CRITICAL_LATIMES_SCRAPER_UNEXPECTED", 
                    "exception": x
                })
            finally:
                driver.close()
                return news_formated

    def build_URI(self, page=1):

        uri = self.base_uri

        if self.query:
            uri += f"&q={self.query}"

        if len(self.news_topics_UUID) > 0:
            uri += "".join(list(map(lambda uuid: f"&f0={uuid}", self.news_topics_UUID)))

        if len(self.news_types_UUID) > 0:
            uri += "".join(list(map(lambda uuid: f"&f1={uuid}", self.news_types_UUID)))

        uri += f"&p={page}"

        log.debug("", {
            "event": "DEBUG_LATIMES_NEW_URI", 
            "uri": uri
        })

        return uri

    def get_params_from_robocorp(self, variables):

        log.debug("", {
            "event": "DEBUG_LATIMES_VARIABLES", 
            "variables": variables
        })

        for variable, value in variables.items():
            match variable:
                case "query":
                    self.query = value
                case "topics":
                    self.news_topics = value.strip().lower().split(",")
                case "types":
                    self.news_types = value.strip().lower().split(",")
                case "months_count":
                    self.months_count = int(value)

                    self.max_timestamp = datetime.today()
                    self.max_timestamp = self.max_timestamp.replace(
                        day=1,
                        hour=0,
                        minute=0,
                        second=0, 
                        microsecond=0
                    )

                    if value > 1:
                        self.max_timestamp = self.max_timestamp - relativedelta(months = value - 1)

                    self.max_timestamp = self.max_timestamp.timestamp()

        log.debug("", {
            "event": "DEBUG_LATIMES_VARIABLES_FORMATED",
            "variables": variables,
            "query":self.query,
            "news_topics": self.news_topics,
            "news_types": self.news_types,
            "months_tount": self.months_count,
            "max_timestamp": self.max_timestamp
        })