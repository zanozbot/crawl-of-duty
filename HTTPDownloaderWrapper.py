from HTTPDownloader import *
import multiprocessing
# Selenium
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from tools import platform_driver, chrome_options

driver_list = dict()
def processSiteUrlWrapper(url, robotsparser):
    # This process id
    pid = multiprocessing.current_process().pid
    
    # Last time it is called
    # kill driver
    if url is None :
        if pid in driver_list:
            driver = driver_list.pop(pid)
            driver.quit()
        return {}

    # Access chrome instance coupled with this worker
    # or create if not running
    driver = None
    if pid not in driver_list:
        driver = driver_list[pid] = webdriver.Chrome(executable_path=platform_driver, options=chrome_options)
        driver.set_page_load_timeout(5)
        driver.implicitly_wait(5)
    else:
        driver = driver_list[pid]

    return processSiteUrl(url, robotsparser, driver)