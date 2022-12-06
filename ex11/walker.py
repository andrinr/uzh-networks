from enum import Enum

class Walker:
    def __init__(
            self, 
            id : int,  
            position : int, 
            is_infected : bool):
        """ 
        Initialize a walker object.

        Parameters:
        ----------
        id : int
            unique id of the walker
        position : int
            current position of the walker
        infection_status : bool
            True if walker is infected, False otherwise
        """
        self.id = id
        self.position = position
        self.is_infected = is_infected
