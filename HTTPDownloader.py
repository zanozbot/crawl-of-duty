from bs4 import BeautifulSoup
import aiohttp
import sys, re, atexit
import xml.etree.ElementTree as ET
from tools import *
import sys
import tldextract


# return a dictionary with appropriate values
# "add_to_frontier" should be an array of urls found on the website.
# They do not need to be canonized, that is taken care of in processing.py
# other keys are optional. For each key a callback can be specified that
# gets called when returned. An example of that is in Crawler.py
def processSiteUrl(url, robotsparser, driver):
    # Call appropriate code
    if url.endswith('pdf') \
            or url.endswith('doc') \
            or url.endswith('docx') \
            or url.endswith('doc') \
            or url.endswith('ppt') \
            or url.endswith('pptx'):
        return {"add_to_frontier": [], "website": getBinaryFile(url, robotsparser)}
    else:
        return seleniumGetContents(url, robotsparser, driver)




# async def getSiteContent(url, robotsparser, contentType = ContentType.HTML):
#     async with aiohttp.ClientSession() as session:
#         rp, locations, sitemap = robotsparse(url)
#         if robotsparser.can_fetch("*", url):
#             if contentType == ContentType.HTML:
#                 async with session.get(url) as resp:
#                     text = await resp.read()
#                     print(text)
#             elif contentType == ContentType.HEAD:
#                 async with session.get(url) as resp:
#                     text = resp.headers
#         else:
#             return ""

#     if contentType == ContentType.HTML:
#         # print(BeautifulSoup(text.decode('utf-8'), 'html5lib'))
#         htmlContent = BeautifulSoup(text.decode('utf-8'), 'html5lib')
#         documents = []
#         images = []
#         for link in htmlContent.find_all('img'):
#             current_link = link.get('src')
#             if current_link:
#                 images.append(current_link)
#         for link in htmlContent.find_all('a'):
#             current_link = link.get('href')
#             if current_link :
#                 if current_link.endswith('pdf') \
#                             or current_link.endswith('doc') \
#                             or current_link.endswith('docx') \
#                             or current_link.endswith('doc') \
#                             or current_link.endswith('ppt') \
#                             or current_link.endswith('pptx'):
#                     documents.append(current_link)
#         return htmlContent, documents, images
#     elif contentType == ContentType.HEAD:
#         # print(text.decode('utf-8'))
#         return text, [], []



def seleniumGetContents(url, robotsparser, driver):
    driver.get(url)
    htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
    # print(htmlContent)
    add_to_frontier = []
    images = []
    rp, locations, sitemap = robotsparse(url)
    if robotsparser.can_fetch("*", url):
        for link in htmlContent.find_all('img'):
            current_link = link.get('src')
            if current_link:
                images.append(getBinaryFile(current_link, robotsparser))
        for link in htmlContent.find_all('a'):
            current_link = link.get('href')
            
            if current_link:
                link_extract = tldextract.extract(current_link)
                if link_extract.suffix == 'gov':
                    add_to_frontier.append(current_link)

        driver.close()
    return {"add_to_frontier" : add_to_frontier, "website" : htmlContent, "images" : images}

async def getBinaryFile(url, robotsparser):
    async with aiohttp.ClientSession() as session:
        rp, locations, sitemap = robotsparse(url)
        if robotsparser.can_fetch("*", url):
            async with session.get(url) as resp:
                text = await resp.read()
                return text 

print (seleniumGetContents())