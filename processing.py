# THREAD POOL
# Concurrent futures thread pool
import concurrent.futures
# Import synchronized Queue
from multiprocessing import Queue
# Import all ORM models
from database.models import *
import sys, time, atexit
from tools import *

# Pool wrapper
class WrappedPool:
    def __init__(self, func, max_workers, max_size, session):
        # Number of active workers
        self.max_workers = max_workers

        # Max number of urls in queue to be processed
        self.max_size = max_size

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

    # Bind a dictionary of robotparsers
    def bind_robotparsers(self, rp_dict):
        self.rp_dict = rp_dict

    # Bind a session
    def bind_session(self, sess):
        self.session = sess

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
        self.exec()

    # Start pool with frontier
    def start_with_frontier(self):
        self.load_frontier()
        self.exec()

    # Execute pool process
    def exec(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Make safe robotparser pass
            safe_rp = get_robotparser('')
            make_safe_rp = lambda rp_url: self.rp_dict[get_domain(rp_url)] if self.rp_dict is not None and get_domain(rp_url) in self.rp_dict else safe_rp
            try:
                if len(self.params_list) > self.max_size:
                    for parm in self.params_list[self.max_size:]:
                        self.frontier.put(parm)
                    self.params_list = self.params_list[:self.max_size]
                futures = {executor.submit(self.func, canonize_url(params), make_safe_rp(params) ): params for params in self.params_list}
                while futures:
                    fin,nfin = concurrent.futures.wait(futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                    if len(fin) > 0:
                        for f in list(fin):
                            popped = futures.pop(f,None)
                            if popped is not None:
                                self.processed.add(popped)
                            res = f.result()
                            if ("add_to_frontier" in res):
                                for prm in res["add_to_frontier"]:
                                    cprm = canonize_url(prm)
                                    cprm_not_in_db = self.session.query(Page).filter(Page.url == cprm).count() <= 0
                                    if cprm_not_in_db and cprm not in self.processed:
                                        self.frontier.put(cprm)
                                res["add_to_frontier"] = [self.canonize_url(pr) for pr in res["add_to_frontier"]]
                            for k in res:
                                if (k in self.callback):
                                    self.callback[k](popped, res[k])
                            
                    
                    print("\033[K",end='\r')
                    print("Current frontier size:", str(self.frontier.qsize()), end='\r')
                    
                    while not self.frontier.empty() and len(futures) < self.max_size:
                        prms = self.frontier.get()
                        futures[executor.submit(self.func, canonize_url(prms), make_safe_rp(prms))] = prms

                for l in range(self.max_size):
                    executor.submit(self.func, None, None)

            except concurrent.futures.process.BrokenProcessPool as ex:
                print(ex)
                

# Pool creation function
def create_pool_object(func, max_workers=4, max_size=16, session=None):
    return WrappedPool(func, max_workers, max(max_size, max_workers), session)