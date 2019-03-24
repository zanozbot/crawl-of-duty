from database.models import *
from urllib.parse import urlparse
from processing import WrappedPool, create_pool_object
import re

# List of seed urls
seed_list = [""]

class Crawler:
    def __init__(self):
        # Create session from Session object
        session = Session()

        # Create process pool
        pool = create_pool_object(lambda x: {"add_to_frontier" : []}, session=session)
        
        # Register callbacks
        pool.register_callback("processed", lambda x: print(x))
        pool.register_callback("add_to_frontier", lambda x: print(x))

        # DELETE
        session.add_all([Frontier(url="asdasdasd"),Frontier(url="ae")])
        session.commit()

        # Get the number of urls in frontier
        rows = session.query(Frontier).count()

        # Load from database or start with seed lsit
        if rows > 0:
            pool.start_with_frontier()
        else:
            pool.start_with_parameters_list(seed_list)

        
        #print(DataType(code="PDF").code)

    def normalize_url(self, url):
        parsed_url = urlparse(url)
        exploded_path = re.search("(.*\/)(.+)(\..+)", parsed_url.path)
        return parsed_url.scheme + "://" + parsed_url.hostname + exploded_path[1] + exploded_path[2]


Crawler()