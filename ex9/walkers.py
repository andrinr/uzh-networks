import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import scipy
import random
import queue 

class Simulation:
    def __init__(
            self, 
            n_walkers : int,
            G : nx.Graph, 
            lambda_ : float, 
            t_end : int, 
            start_node : int = -1):

        self.G = G
        self.lambda_ = lambda_
        self.t_end = t_end
        self.n_walkers = n_walkers

        self.node_log = []
        self.walker_log = []
        self.timeline = []
        self.t = 0
        
        self.initialize_events(start_node=start_node)
        self.store_results()

    def run(self):

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
            #print(self.t, self.positions[id])
            # update waiting time
            self.times[id] = self.t + np.random.exponential(1/self.lambda_)
            # add new event
            self.queue.put_nowait((self.times[id], id))

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

def sample_ER(N, p):
    rd = np.random.rand(N,N)
    A = np.triu(rd < (p))
    np.fill_diagonal(A, 0)
    return A
    
def gen_com_graph(N, n_coms, p_high, p_low):
    N_pc = int(N / n_coms)
    A_struct = np.zeros((N,N))
    for i in range(n_coms):
        A_struct[i*N_pc:(i+1)*N_pc, i*N_pc:(i+1)*N_pc] = sample_ER(N_pc, p_high)
    A_random = sample_ER(N, p_low)
    A = A_struct + A_random
    

    return nx.from_numpy_matrix(A), A_struct, A_random

