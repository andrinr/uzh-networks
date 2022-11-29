import networkx as nx
import numpy as np
import queue 
import random

# I did not include a explicit single walker version as this one can be used with a single node as well
# Furhtermore, the initialize_events functions is called when the simulation instance is created, which I think makes more sense
# then the run function is sepparated from the initialization
class Simulation:
    def __init__(
            self, 
            n_walkers : int,
            G : nx.Graph, 
            lambda_ : float, 
            t_end : int, 
            start_node : int = -1):

        self.n_walkers = n_walkers
        self.G = G

        self.lambda_ = lambda_

        self.t, self.t_end = 0, t_end

        self.node_log, self.walker_log, self.timeline = [], [], []

        self.initialize_events(start_node=start_node)
        self.store_results()

    def run(self, storage_interval : float = 1):

        checkpoint = 0
        while self.t < self.t_end:
            # get next event
            self.t, id = self.queue.get_nowait()
            
            # move walker
            neighbours = list(self.G.neighbors(self.positions[id]))

            if len(neighbours) == 0:
                self.times[id] = np.inf
                self.queue.put_nowait((self.times[id], id))
                continue

            self.positions[id] = neighbours[random.randint(0, len(neighbours)-1)]

            # update waiting time
            self.times[id] = self.t + np.random.exponential(1/self.lambda_)
            # add new event
            
            #elif self.RW_type == 'edge-centric':
            
            #tau = np.random.exponential(1/(self.lambda_ * self.G.degree(walker.position)))
            
            self.queue.put_nowait((self.times[id], id))

            # results are only stored after a certain time interval
            # this greatly reduces the memory footprint (and repsectively the runtime)
            if self.t - checkpoint > storage_interval:
                checkpoint = self.t
                self.store_results()

        self.node_log = np.stack(self.node_log, axis=0)
        self.walker_log = np.stack(self.walker_log, axis=0)
        
    def initialize_events(self, start_node : int =-1):
        # init random positions for each walker
        if start_node == -1:
            self.positions = np.random.randint(0, self.G.number_of_nodes(), self.n_walkers)
        else:
            self.positions = np.full(self.n_walkers, start_node)
        self.times =  np.random.exponential(1/self.lambda_, self.n_walkers)
        # populate queue with events
        self.queue = queue.PriorityQueue()
        for i in range(self.n_walkers):
            self.queue.put_nowait((self.times[i], i))

    def store_results(self):
        # store the results of the simulation
        self.walker_log.append(self.positions.copy())
        self.node_log.append(np.bincount(self.positions, minlength=self.G.number_of_nodes()))
        self.timeline.append(self.t)
