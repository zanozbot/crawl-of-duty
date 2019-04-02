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
from time import sleep

# return a dictionary with appropriate values
# "add_to_frontier" should be an array of urls found on the website.
# They do not need to be canonized, that is taken care of in pool.py
# other keys are optional. For each key a callback can be specified that
# gets called when returned. An example of that is in Crawler.py
def processSiteUrl(url, robotsparser, driver):
    # Call appropriate code
    time = datetime.now()

    # Shouldn't be, but just in case
    if robotsparser is None:
        rp, sm = robotsparse(url)
        robotsparser = get_robotparser(rp)

    mime_type = ""
    # Follow redirects, get mimetype otherwise
    try:
        response = requests.head(url, timeout=10)
        mime_type = get_mime_type_from_header(response.headers)
    except:
        if url.endswith("pdf"):
            mime_type=".pdf"
        elif url.endswith("ppt"):
            mime_type=".ppt"
        elif url.endswith("pptx"):
            mime_type=".pptx"
        elif url.endswith("doc"):
            mime_type=".doc"
        elif url.endswith("docx"):
            mime_type=".docx"
        else:
            mime_type=".html"
    document_mimes = {'.doc','.docx','.ppt','.pptx','.pdf'}
    
    if mime_type is not None and mime_type in document_mimes:
        # COMMENT THIS LINE ON SECOND RUN!
        file_content, headers, status_code = getBinaryFile(url, robotsparser)
        if headers is None:
            return {}
        # COMMENT THIS LINE ON SECOND RUN!
        return {"document": {"content": file_content, "page_type": "BINARY", "status_code": status_code, "data_type": ending_to_datatype(get_mime_type_from_header(headers)), "time_accessed": time}}
        # UNCOMMENT THIS LINE ON SECOND RUN!
        # return {}
    elif mime_type is not None and ending_to_datatype(mime_type) == 'HTML':
        return seleniumGetContents(url, robotsparser, driver)
    else:
        return {}

def seleniumGetContents(url, robotsparser, driver):
    add_to_frontier = []
    images = []
    text =""
    headers=dict()
    status_code = 204

    if robotsparser.can_fetch("*", url):
        try:
            driver.get(url)
        except TimeoutException as ex:
            print("WEBSITE TOOK TOO LONG TO RESPOND:", url)
            return {}

        htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
        time_accessed = datetime.now()
        try:
            response = requests.head(url, timeout=10)
            status_code = response.status_code
            headers = response.headers
            if status_code is None:
                status_code = 204
        except:
            pass

        # COMMENT THIS WHOLE BLOCK ON SECOND RUN!
        for link in htmlContent.find_all('img'):
            current_link = link.get('src')
            if current_link:
                extracted_url = tldextract.extract(current_link)
                # TODO: Check if this is good for all. Add try catch block?
                if extracted_url.suffix != 'data' and extracted_url.domain != 'cms':
                    try:
                        text, headers, status_code = getBinaryFile(canonize_url(current_link,url), robotsparser)
                        if text is not None and headers is not None and status_code is not None:
                            images.append((text, headers, status_code, datetime.now(), current_link, current_link[current_link.rfind("/")+1:]))
                    except:
                        pass
                elif extracted_url == 'data':
                    images.append([current_link, {"Content-Type" : current_link}, status_code, time_accessed, ""])
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
        
        return {"add_to_frontier" : add_to_frontier, "website" : {"content": str(htmlContent), "status_code": status_code, "page_type": "HTML", "images": images, "time_accessed": time_accessed}}
    return {}

def getBinaryFile(url, robotsparser):
    try:
        if robotsparser.can_fetch("*", url):
            response = requests.get(url, timeout=30)
            return response.text, response.headers, response.status_code
        else:
            return None, None, None
    except:
        return None, None, None

def temp(url):
    try:
        response = requests.get(url, timeout=30)
        return response.text, response.headers, response.status_code
    except:
        return None, None, None
