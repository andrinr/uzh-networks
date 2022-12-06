import networkx as nx
import numpy as np
import queue 
import random
from enum import Enum
from walker import Walker

class Recorder:
    def __init(self, duration : float, interval : float):
        self.duration = duration
        self.interval = interval
        self.data = []
        self.time = 0.0


class Event(Enum):
    RECOVER = 1
    INFECT = 2
    JUMP = 3

class Simulation:
    def __init__(
            self, 
            G : nx.Graph, 
            D_S : float = 0.1,
            D_I : float = 0.1,
            beta : float = 0.1,
            mu : float = 0.01):
        """
        Initialize the simulation
        
        Parameters:
        -----------
        G : nx.Graph
            The graph on which the walkers are moving
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

        self.t = 0
        self.D_S = D_S
        self.D_I = D_I
        self.beta = beta
        self.mu = mu
        self.infected_walkers = np.zeros(self.G.number_of_nodes())
        self.total_walkers = np.zeros(self.G.number_of_nodes())
        self.queue = queue.PriorityQueue()

        # for efficiency reasons the walker positions are stored as an array as well
        self.node_log, self.walker_log, self.infected_log, self.timeline = [], [], [], []

    def run(self, duration = 10, storage_interval : float = 0.1, storage_mode : str = "linear"):
        """
        Run the simulation

        Parameters:
        -----------
        duration : int
            The duration of the simulation
        storage_interval : float
            The interval at which the results are stored

        Returns:
        --------
        self : Simulation
            The simulation instance
        """
        self.__initialize_events()
        self.__store_results()

        end_time = self.t + duration
        checkpoint = 0
        while self.t < end_time:
            self.t, (id, event, next_pos) = self.queue.get_nowait()
            #print(self.t, id, event, next_pos)
            if event == Event.RECOVER:
                self.__set_infection_status(id, False)
            elif event == Event.INFECT:
                self.__set_infection_status(id, True)
            elif event == Event.JUMP:
                self.__jump(id, next_pos)

            self.queue.put_nowait(self.__get_next_event(id))

            # results are only stored after a certain time interval
            # this greatly reduces the memory footprint (and repsectively the runtime)
            if storage_mode == 'linear' and self.t - checkpoint > storage_interval:
                checkpoint = self.t
                self.__store_results()
            
            if storage_mode == 'log' and np.log(self.t) - np.log(checkpoint) > storage_interval:
                checkpoint = self.t
                self.__store_results()

        self.node_log = np.stack(self.node_log, axis=0)
        self.walker_log = np.stack(self.walker_log, axis=0)
        self.infected_log = np.stack(self.infected_log, axis=0)

        return self

    def init_walkers_uniform(self, n_walkers : int):
        """
        Initialize walkers uniformly over all nodes

        Parameters:
        -----------
        n_walkers : int
            The number of walkers

        Returns:
        --------
        self : Simulation
            The simulation instance
        """
        self.n_walkers = n_walkers
        self.positions = np.random.randint(0, self.G.number_of_nodes(), self.n_walkers)
        self.walkers = [Walker(idx, pos, False) for idx, pos in enumerate(self.positions)]
        self.total_walkers = np.bincount(self.positions, minlength=self.G.number_of_nodes())

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

        Returns:
        --------
        self : Simulation
            The simulation instance
        """
        self.n_walkers = n_walkers
        self.positions = np.full(self.n_walkers, node)
        self.walkers = [Walker(idx, pos, False) for idx, pos in enumerate(self.positions)]
        self.total_walkers[node] = n_walkers

        return self

    def infect_walkers(self, percentage : float):
        """
        Infect a certain percentage of the walkers

        Parameters:
        -----------
        percentage : float
            The percentage of walkers that are infected

        Returns:
        --------
        self : Simulation
            The simulation instance
        """
        n_infected = int(self.n_walkers * percentage)
        infected_walkers = np.random.choice(self.n_walkers, n_infected, replace=False)
        #print(infected_walkers)
        for id in infected_walkers:
            self.__set_infection_status(id, True)

        return self

    def __initialize_events(self):
        """
        Initialize the events for the simulation
        """
        for walker in self.walkers:
            self.queue.put_nowait(self.__get_next_event(walker.id))

    def __jump(self, id : int, new_position : int):
        """
        Moves a walker to a new position and updates datastructures

        Parameters:
        -----------
        id : int
            The id of the walker
        new_position : int 
            The new position of the walker
        """
        walker = self.walkers[id]

        self.total_walkers[walker.position] -= 1
        self.total_walkers[new_position] += 1

        if walker.is_infected:
            self.infected_walkers[walker.position] -= 1
            self.infected_walkers[new_position] += 1

        walker.position = new_position
        self.positions[id] = new_position
        #print(self.positions[id])

    def __set_infection_status(self, id : int, status : bool):
        """
        Change the infection status of a walker

        Parameters:
        -----------
        id : int
            The id of the walker
        status : bool
            The new infection status of the walker
        """
        walker = self.walkers[id]
        prev_status = walker.is_infected
        if prev_status == True and status == False:
            self.infected_walkers[walker.position] -= 1
        elif prev_status == False and status == True:
            self.infected_walkers[walker.position] += 1
        walker.is_infected = status

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

        jump_time = self.t + \
            np.random.exponential(self.D_I if walker.is_infected else self.D_S)
        recovery_time = self.t + np.random.exponential(self.mu)
        infection_time = self.t + \
            np.random.exponential(self.beta * self.infected_walkers[walker.position])

        if walker.is_infected and recovery_time < jump_time:
            # recover
            return (recovery_time, (id, Event.RECOVER, walker.position))
        elif not walker.is_infected and infection_time < jump_time:
            # get infected
            return (infection_time, (id, Event.INFECT, walker.position))
        else:
            # jump
            pos = walker.position
            if len(self.G[pos]) == 0:
                return (np.inf, (id, pos))

            new_pos = random.choice(list(self.G[pos]))
            return jump_time, (id,  Event.JUMP, new_pos)

    def __store_results(self):
        """
        Store the current state of the simulation
        """
        self.walker_log.append(self.positions.copy())
        self.node_log.append(self.total_walkers.copy())
        self.infected_log.append(self.infected_walkers.copy())
        self.timeline.append(self.t)
