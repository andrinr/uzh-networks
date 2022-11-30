import networkx as nx
import numpy as np
import queue 
import random
from enum import Enum
from walker import Walker

class Change(Enum):
    RECOVER = 1
    INFECT = 2
    JUMP = 3

# I did not include a explicit single walker version as this one can be used with a single node as well
# Furhtermore, the initialize_events functions is called when the simulation instance is created, which I think makes more sense
# then the run function is sepparated from the initialization
class Simulation:
    def __init__(
            self, 
            G : nx.Graph, 
            lambda_ : float, 
            t_end : int, 
            D_S : float = 0.0,
            D_I : float = 0.0,
            beta : float = 0.0,
            mu : float = 0.0):
        """
        Initialize the simulation
        
        Parameters:
        -----------
        G : nx.Graph
            The graph on which the walkers are moving
        lambda_ : float
            The rate at which the walkers move
        t_end : int
            The time at which the simulation ends
        D_S : float
            The rate at which susceptible walkers are infected
        D_I : float
            The rate at which infected walkers recover
        beta : float
            The rate at which infected walkers infect susceptible walkers
        mu : float
            The rate at which walkers die
        """
        self.walkers = []
        self.G = G

        self.lambda_ = lambda_

        self.t, self.t_end = 0, t_end
        self.D_S = D_S
        self.D_I = D_I
        self.beta = beta
        self.mu = mu
        self.infected_walkers = np.zeros(self.G.number_of_nodes())
        self.queue = queue.PriorityQueue()

        # for efficiency reasons the walker positions are stored as an array as well
        self.node_log, self.walker_log, self.timeline = [], [], []

    def run(self, storage_interval : float = 1):
        """
        Run the simulation

        Parameters:
        -----------
        storage_interval : float
            The interval at which the results are stored
        """
        self.__initialize_events()
        self.__store_results()

        checkpoint = 0
        while self.t < self.t_end:
            self.t, (id, next_pos) = self.queue.get_nowait()
            
            self.__move_walker(id, next_pos)
            self.queue.put_nowait(self.__get_next_event(id))

            # results are only stored after a certain time interval
            # this greatly reduces the memory footprint (and repsectively the runtime)
            if self.t - checkpoint > storage_interval:
                checkpoint = self.t
                self.__store_results()

        self.node_log = np.stack(self.node_log, axis=0)
        self.walker_log = np.stack(self.walker_log, axis=0)

        return self

    def init_walkers_uniform(self, n_walkers : int):
        """
        Initialize walkers uniformly over all nodes

        Parameters:
        -----------
        n_walkers : int
            The number of walkers
        """
        self.n_walkers = n_walkers
        self.positions = np.random.randint(0, self.G.number_of_nodes(), self.n_walkers)
        self.walkers = [Walker(idx, pos, False) for idx, pos in enumerate(self.positions)]

        return self

    def init_walkers_single_node(self, n_walkers : int, node : int):
        """
        Initialize walkers on a single node

        Parameters:
        -----------
        n_walkers : int
            The number of walkers
        node : int
            The node where all walkers are initialized
        """
        self.n_walkers = n_walkers
        self.positions = np.full(self.n_walkers, node)
        self.walkers = [Walker(idx, pos, False) for idx, pos in enumerate(self.positions)]

        return self

    def infect_walkers(self, percentage : float):
        """
        Infect a certain percentage of the walkers

        Parameters:
        -----------
        percentage : float
            The percentage of walkers that are infected
        """
        n_infected = int(self.n_walkers * percentage)
        infected_walkers = np.random.choice(self.n_walkers, n_infected, replace=False)
        for id in infected_walkers:
            self.__change_infection_status(id, True)

        return self

    def __initialize_events(self):
        """
        Initialize the events for the simulation
        """
        for walker in self.walkers:
            self.queue.put_nowait(self.__get_next_event(walker.id))

    def __move_walker(self, id : int, new_position : int):
        """
        Moves a walker to a new position

        Parameters:
        -----------
        id : int
            The id of the walker
        new_position : int 
            The new position of the walker
        """
        walker = self.walkers[id]
        walker.position = new_position
        self.positions[id] = new_position

    def __change_infection_status(self, id : int, status : bool):
        """
        Change the infection status of a walker

        Parameters:
        -----------
        id : int
            The id of the walker
        status : bool
            The new infection status of the walker
        """
        if status == True:
            self.infected_walkers.append(id)

        self.walkers[id].infection_status = status
  
        
    def __get_next_event(self, id : int) -> tuple:
        """
        Get the next event for a walker
        
        Parameters:
        -----------
        id : int
            The id of the walker
            
        Returns:
        --------
        t : float
            The time of the next event
        (id, new_pos) : (int, int)
            The id of the walker and the new position of the walker
        """
        walker = self.walkers[id]

        jump_time = self.t + np.random.exponential(1 / self.lambda_)
        recovery_time = self.t + np.random.exponential(1 / self.D_I)
        infection_time = self.t + np.random.exponential(1 / self.D_S)

        if walker.is_infected and recovery_time < jump_time:
            # recover
            return (recovery_time, (id, walker.position, Change.RECOVER))
        elif not walker.is_infected and infection_time < jump_time:
            # infect
            return (infection_time, (id, walker.position, Change.INFECT))
        else:
            # jump
            pos = walker.position
            if len(self.G[pos]) == 0:
                return (np.inf, (id, pos))

            new_pos = random.choice(list(self.G[pos]))
            return jump_time, (id, new_pos, Change.JUMP)

    def __store_results(self):
        """
        Store the current state of the simulation
        """
        self.walker_log.append(self.positions.copy())
        self.node_log.append(np.bincount(self.positions, minlength=self.G.number_of_nodes()))
        self.timeline.append(self.t)
