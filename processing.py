# THREAD POOL
# Concurrent futures thread pool
import concurrent.futures
# Import synchronized Queue
from multiprocessing import Queue
# Import all ORM models
from database.models import *
import sys, time, atexit, url


# Pool wrapper
class WrappedPool:
    def __init__(self, func, max_workers, max_size, session):
        # Number of active workers
        self.max_workers = max_workers

        # Session object
        self.session = session
        
        # Function to execute
        self.func = func

        # Parameter list
        self.params_list=[]

        # Frontier
        self.frontier = Queue()

        # Set of processed urls
        self.processed = set()

        # Callback dictionary
        self.callback = dict()

        # Register frontier save function at program exit
        atexit.register(self.save_frontier)
    
    # Url canonization
    def canonize_url(self, url_string):
        url_parsed = url.URL.parse(url_string)
        url_cleaned = url_parsed.strip().defrag().deparam(['utm_source']).abspath().escape().canonical().utf8
        return url_cleaned

    # Load frontier
    def load_frontier(self):
        rows = self.session.query(Frontier).all()
        self.params_list = [row.url for row in rows]
        self.session.query(Frontier).delete()
        self.session.commit()

    # Save frontier
    def save_frontier(self):
        ls = list()
        while not self.frontier.empty():
            ls.append(Frontier(url=self.frontier.get()))
        self.session.add_all(ls)
        self.session.commit()

    # Callback registration
    def register_callback(self, c_type, func):
        self.callback[c_type] = func

    # Start pool with parameters to pass to function
    def start_with_parameters(self, *params):
        self.params_list.append(params)
        self.exec()

    # Start pool with a list of parameters to pass to function
    def start_with_parameters_list(self, params):
        for param in params:
            self.params_list.append(param)
        #self.exec()

    # Start pool with frontier
    def start_with_frontier(self):
        self.load_frontier()
        #self.exec()

    def exec(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:            
            try:
                futures = {executor.submit(self.func, self.canonize_url(params) ): params for params in self.params_list}
                while futures:
                    fin,nfin = concurrent.futures.wait(futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                    if len(fin) > 0:
                        for f in list(fin):
                            futures.pop(f,None)
                            res = f.result()
                            if ("add_to_frontier" in res):
                                for prm in res["add_to_frontier"]:
                                    cprm = canonize_url(prm)
                                    if cprm not in self.processed:
                                        self.frontier.put(cprm)
                            for k in res:
                                if (k in self.callback):
                                    self.callback[k](res[k])
                            
                    
                    print("\033[K",end='\r')
                    print("Current frontier size:", str(self.frontier.qsize()), end='\r')
                    
                    while not self.frontier.empty() and len(futures) < self.max_size:
                        prms = self.frontier.get()
                        futures[executor.submit(self.func, canonize_url(prms))] = prms

                        
            except concurrent.futures.process.BrokenProcessPool as ex:
                print(ex)
                

# Pool creation function
def create_pool_object(func, max_workers=4, max_size=20, session=None):
    return WrappedPool(func, max_workers, max_size, session=(Session() if session is None else session) )
