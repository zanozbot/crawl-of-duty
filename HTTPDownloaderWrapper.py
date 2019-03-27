from HTTPDownloader import *
import multiprocessing
# Selenium
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

# Drivers linux/windows/osx
platform_driver = ''
if sys.platform.startswith('linux'):
    platform_driver = './platform_dependent/linux_chromedriver'
elif sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
    platform_driver = './platform_dependent/win_chromedriver.exe'
elif sys.platform.startswith('darwin'):
    platform_driver = './platform_dependent/osx_chromedriver'

# Chrome execute arguments
chrome_options = Options()
chrome_options.add_argument("--headless")

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
    else:
        driver = driver_list[pid]

    return processSiteUrl(url, robotsparser, driver)