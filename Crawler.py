from database.models import *
from urllib.parse import urlparse
from processing import WrappedPool, create_pool_object
import re
from tools import *

# List of seed urls
seed_list = [
    # Compulsory
    "http://evem.gov.si",
    "http://e-uprava.gov.si",
    "http://podatki.gov.si",
    "http://e-prostor.gov.si",
    # Selected
    "http://arso.gov.si",
    "http://gu.gov.si",
    "http://mop.gov.si",
    "http://mju.gov.si",
    "http://ess.gov.si"
]

class Crawler:
    def __init__(self):
        # Create session from Session object
        self.session = Session()

        seedObjs = []
        for seed in seed_list:
            rp, locations, sitemap = robotsparse(seed)
            s = Site(domain=seed, robots_content=str(rp), sitemap_content=sitemap)
            if self.session.query(Frontier).filter(Frontier.domain == seed).count() <= 0:
                self.session.add(s)
                self.session.commit()

        print(self.session.query(Frontier))

        exit(1)

        # Create process pool
        pool = create_pool_object(lambda x: {"add_to_frontier" : []}, session=self.session)
        
        # Register callbacks
        # "website" expects a list with appropriate data
        pool.register_callback("website", self.process_website)
        # "add_to_frontier" contains same data as used by processing.py. 
        # It is a list of links
        pool.register_callback("add_to_frontier", self.process_links)
        # "documents" contains an array of documents
        pool.register_callback("documents", self.process_documents)
        # "images" contains an array of images
        pool.register_callback("images", self.process_images)

        # Get the number of urls in frontier
        rows = self.session.query(Frontier).count()

        # Load from database or start with seed lsit
        if rows > 0:
            pool.start_with_frontier()
        else:
            pool.start_with_parameters_list(seed_list)

    def process_links(self, url, links):
        links = [canonize_url(link) for link in links]
        linkObjs = [Link(from_page=url, to_page=link) for link in links]
        self.session.add_all(linkObjs)
        self.session.commit()

    def process_website(self, url, website):

        print(website)

    def process_documents(self, url, documents):
        print(documents)

    def process_images(self, url, images):
        print(images)

Crawler()