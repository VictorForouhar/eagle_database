from numpy import where, arange
from .helper_functions import quick_search

class Subgroup():

    def __init__(self, database, subgroup_number, snap_number):
        """
        Creates a Sugroup object used to retrieve information about its past
        evolution.

        Parameters
        -----------
        database : ObjectType
            Object initialised through the Database class where the Subgroup of
            interest is located
        subgroup_number : int
            Number of the subgroup to track. This is the absolute position in the 
            catalogue, e.g. not the relative position within a single Subfind table
            file.
        snap_number : int
            Snapshot number that this subgroup is located in. 

        Returns
        --------
        None
        """

        self._database         = database
        self._subgroup_number  = subgroup_number
        self._snap_number      = snap_number

        # Finding unique identifiers for specified group
        self._positional_index = self.get_positional_index() 
        self._nodeIndex        = self.get_nodeIndex()
        self._galaxyID         = self.get_galaxyID()
        self._topLeafID        = self.get_topLeafID()
        
        # Retrieving progenitors along the main branch
        self._main_progenitors = self.get_main_progenitors()

        # Dict where property evolution is stored. Perhaps redshifts should
        # be included here
        self.evolution = {}

    def get_positional_index(self):
        '''
        Returns the array index where the object of interest is stored
        '''
        return where(self._database['Subhalo/SnapNum'] == self._snap_number)[0][self._subgroup_number]

    def get_nodeIndex(self):
        '''
        Returns the nodeIndex of the tracked subgroup, given by
        the combination:
        snap_number * 1e12 + file_number * 1e8 + subgroup_number_in_file
        '''
        return self._database['MergerTree/nodeIndex'][self._positional_index]

    def get_galaxyID(self):
        '''
        Returns the unique identifier as given in the depth-first database
        '''
        return self._database['MergerTree/GalaxyID'][self._positional_index]
    
    def get_topLeafID(self):
        return self._database['MergerTree/TopLeafID'][self._positional_index]

    def get_main_progenitors(self):
        '''
        Returns the main progenitors of the subgroup
        '''
        return arange(self._galaxyID,self._topLeafID+1) 
    
    def get_property_evolution(self, property):
        '''
        Retrieves main progenitor branch evolution of specified property.
        
        Parameters
        -----------
        property: str
            Name of the property to retrieve
        '''
        if property not in self.evolution:
            self.evolution[property] = self._database['Subhalo/%s'%property][()][self._main_progenitors]

        return self.evolution[property]

    @property
    def positional_index(self):
        return self._positional_index
    
    @property
    def nodeIndex(self):
        return self._nodeIndex
    
    @property
    def galaxyID(self):
        return self._galaxyID
    
    @property
    def topLeafID(self):
        return self._topLeafID
    
    @property
    def main_progenitors(self):
        return self._main_progenitors