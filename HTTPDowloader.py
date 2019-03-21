from bs4 import BeautifulSoup
import aiohttp
import asyncio
import urllib

URL = 'http://e-uprava.gov.si'

def __init__(self, URL):
    self.URL = URL

async def getSiteContent(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.read()

    print(BeautifulSoup(text.decode('utf-8'), 'html5lib'))
    return BeautifulSoup(text.decode('utf-8'), 'html5lib')

async def robotsAllow(url):
    return False

asyncio.run(getSiteContent(URL))