import datetime
import errno
import os
import re
import requests
import uuid


class News():


    def __init__(self, title, timestamp, description, picture_SRC, query) -> None:

        self.title = title
        self.date = datetime.datetime.fromtimestamp(timestamp) if timestamp else None
        self.description = description
        self.count_query_match_value = 0
        self.picture = None
        self.has_money = False

        self.check_for_money()
        
        if(picture_SRC):
            self.pictureSRC = picture_SRC
            self.download_image()
        
        if query:
            self.count_query_match(query)

    def to_dict(self):

        return {
            "title": self.title,
            "date": self.date,
            "description": self.description,
            "picture": self.picture,
            "count_query_match": self.count_query_match_value,
            "has_money": "TRUE" if self.has_money else "FALSE",
        }

    def download_image(self):

        filename = f"{uuid.uuid4()}.png"
        file_path = f"output/images/{filename}"

        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        image = requests.get(self.pictureSRC).content
        with open(file_path, "wb") as handler:
            handler.write(image)
        
        self.picture = filename

    def count_query_match(self, query):

        self.count_query_match_value = len(re.findall(r"\b" + re.escape(query) + r"\b", f"{self.title} {self.description}", flags=re.IGNORECASE))
        return self.count_query_match_value

    def check_for_money(self):

        dollar_sign_pattern = r"\$(?:\d+,?)+\.\d{0,2}"
        dollar_text_pattern = r"\d+ dollars?"
        usd_pattern = r"\d+ USD"

        dollar_sign_search = re.search(dollar_sign_pattern, f"{self.title} {self.description}", flags=re.IGNORECASE)
        dollar_text_search = re.search(dollar_text_pattern, f"{self.title} {self.description}", flags=re.IGNORECASE)
        usd_search = re.search(usd_pattern, f"{self.title} {self.description}", flags=re.IGNORECASE)

        self.has_money = bool(dollar_sign_search or dollar_text_search or usd_search)
        return self.has_money