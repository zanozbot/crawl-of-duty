from database.models import *
from urllib.parse import urlparse
from pool import WrappedPool, create_pool
import re
from tools import *
from datetime import datetime
from tools import get_domain
import hashlib
from multiprocessing import freeze_support

# List of seed urls
seed_list = [
    # Compulsory
    "evem.gov.si",
    "e-uprava.gov.si",
    "podatki.gov.si",
    "e-prostor.gov.si",
    # Selected
    # "www.arso.gov.si",
    # "www.gu.gov.si",
    # "mop.gov.si",
    # "mju.gov.si",
    # "www.ess.gov.si"
]

class Crawler:
    def __init__(self):
        # Create session from Session object
        print("- INITIALIZING DATABASE CONNECTION -")
        self.session = Session()

        # Get robots.txt and sitemap.xml data if available and not in db
        seedObjs = []
        sites = []
        for seed in seed_list:
            seed = canonize_url(seed)
            if self.session.query(Site).filter(Site.domain == seed).count() <= 0:
                rp, sitemap = robotsparse(seed)
                s = Site(domain=seed, robots_content=rp, sitemap_content=sitemap)
                sites.append(s)

        if len(sites) > 0:
            self.session.add_all(sites)
            self.session.commit()


        # Create process pool
        self.pool = create_pool(session=self.session, max_workers=8, max_size=16)
        if self.pool is None:
            return

        # Get the number of urls in frontier
        rows = self.session.query(Frontier).count()

        # Get all sites and create robotparser dictionary
        sites = self.session.query(Site).all()
        rp_dict = dict()
        for site in sites:
            rp = get_robotparser(site.robots_content)
            rp_dict[get_domain(site.domain)] = rp
        
        # Bind a dictionary of robotparsers
        self.pool.bind_robotparsers(rp_dict)

        # Load from database or start with seed lsit
        if rows > 0:
            self.pool.start_with_frontier()
        else:
            # Get all site data
            seeds = []
            for site in sites:
                seeds.append(site.domain)
                if site.sitemap_content is not None and site.sitemap_content != '':
                    nrmlzd = get_sitemap_locations(site.sitemap_content)
                    for nrm in nrmlzd:
                        seeds.append(nrm)
            self.pool.start_with_parameters_list(seeds)


    

if __name__ == '__main__':
    freeze_support()
    start_time = datetime.now()
    Crawler()
    time_elapsed = datetime.now() - start_time
    print('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))