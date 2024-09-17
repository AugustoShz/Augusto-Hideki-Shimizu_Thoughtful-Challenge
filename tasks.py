import os
import shutil
import zipfile
import pandas as pd
from robocorp.tasks import task
from RPA.Robocorp.WorkItems import WorkItems
from robocorp import log

from classes.scrappers.latimesscrapper import LaTimesScrapper


@task
def minimal_task():


    log.info("Starting Los Angeles Times flow...", {"event": "INFO_LATIMES_START_FLOW"})

    log.info("Getting Work Item variables", {"event": "INFO_LATIMES_START_WORKITEMVARIABLES"})
    library = WorkItems()
    library.get_input_work_item()
    variables = library.get_work_item_variables()
    log.info("Work Item variables were formated successfully", {"event": "INFO_LATIMES_END_WORKITEMVARIABLES"})

    log.info("Starting Los Angeles Times scraping!", {"event": "INFO_LATIMES_START_SCRAPING"})
    scrapper = LaTimesScrapper()
    scrapper.get_params_from_robocorp(variables)
    news_formated = scrapper.get_news()
    log.info("Los Angeles Times scraping ended successfully!", {"event": "INFO_LATIMES_END_SCRAPING"})


    log.info("Saving Excel file and Zipping Images!", {"event": "INFO_LATIMES_START_SAVING"})
    df = pd.DataFrame.from_records(data=[s.to_dict() for s in news_formated], columns=["title", "date", "description", "picture", "count_query_match", "has_money"])
    df.to_excel("output/news.xlsx", sheet_name="News", index=False)
    if os.path.isdir("output/images"):
        zf = zipfile.ZipFile("output/images.zip", "w")
        for dirname, __subdirs, files in os.walk("output/images"):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()
        shutil.rmtree("output/images")
    log.info("Saved filed succesfully!", {"event": "INFO_LATIMES_END_SAVING"})