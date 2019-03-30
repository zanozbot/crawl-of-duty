from bs4 import BeautifulSoup
import aiohttp
import sys, re, atexit
import xml.etree.ElementTree as ET
from tools import *
import sys
import tldextract
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from datetime import datetime
import requests

# return a dictionary with appropriate values
# "add_to_frontier" should be an array of urls found on the website.
# They do not need to be canonized, that is taken care of in processing.py
# other keys are optional. For each key a callback can be specified that
# gets called when returned. An example of that is in Crawler.py
def processSiteUrl(url, robotsparser, driver):
    # Call appropriate code
    time = datetime.now()

    if url.endswith('pdf') \
            or url.endswith('doc') \
            or url.endswith('docx') \
            or url.endswith('ppt') \
            or url.endswith('pptx'):
        # COMMENT THIS LINE ON SECOND RUN!
        file_content, headers, status_code = getBinaryFile(url, robotsparser)
        # COMMENT THIS LINE ON SECOND RUN!
        return {"document": {"content": file_content, "page_type": "BINARY", "status_code": status_code, "data_type": get_datatype_from_header(headers), "time_accessed": time}}
        # UNCOMMENT THIS LINE ON SECOND RUN!
        # return {}
    else:
        return seleniumGetContents(url, robotsparser, driver)


def seleniumGetContents(url, robotsparser, driver):
    add_to_frontier = []
    images = []
    text =""
    headers=dict()

    if robotsparser.can_fetch("*", url):
        try:
            driver.get(url)
        except TimeoutException as ex:
            print("WEBSITE TOOK TOO LONG TO RESPOND:", url)
            return {}

        htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
        time_accessed = datetime.now()

        # COMMENT THIS WHOLE BLOCK ON SECOND RUN!
        for link in htmlContent.find_all('img'):
            current_link = link.get('src')
            if current_link:
                extracted_url = tldextract.extract(current_link)
                # TODO: Check if this is good for all. Add try catch block?
                # WAS NOT CHECKED
                if extracted_url.suffix != 'data' and extracted_url.domain != 'cms':
                    text, headers, status_code = getBinaryFile(canonize_url(current_link,url), robotsparser)
                    if text is not None and headers is not None and status_code is not None:
                        images.append((text, headers, status_code, datetime.now()))
                elif extracted_url == 'data':
                    images.append([current_link, {}, status_code, datetime.now()])
        # END OF BLOCK
        
        for link in htmlContent.find_all('a'):
            current_link = link.get('href')

            if current_link:
                link_extract = tldextract.extract(current_link)
                if link_extract.suffix == 'si' and link_extract.domain == 'gov':
                    # Do not add these to frontier
                    mtch = re.match('.*(?:mailto\:|callto\:|sms\:|tel\:).*',current_link)
                    if mtch is None:
                        add_to_frontier.append(current_link)
        cur_text, headers, status_code = temp(url)
        if status_code is None:
            status_code = 204
        return {"add_to_frontier" : add_to_frontier, "website" : {"content": str(htmlContent), "status_code": status_code, "page_type": "HTML", "images": images, "time_accessed": time_accessed}}
    return {}

def getBinaryFile(url, robotsparser):
    try:
        if robotsparser.can_fetch("*", url):
            response = requests.get(url, timeout=30)
            return response.text, response.headers, response.status_code
    except:
        return None, None, None

def temp(url):
    try:
        response = requests.get(url, timeout=30)
        return response.text, response.headers, response.status_code
    except:
        return None, None, None
