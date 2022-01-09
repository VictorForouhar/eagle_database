from numpy import where, arange, asarray, hstack
import matplotlib.pyplot as plt
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

        #-------------------------------------------------------------------------
        # Setting basic properties of this subgroup
        #-------------------------------------------------------------------------
        self._database         = database
        self._subgroup_number  = subgroup_number
        self._snap_number      = snap_number

        #-------------------------------------------------------------------------
        # Retrieve additional properties required to get time evolution of
        # propenitors/descendants of this subgroup
        #-------------------------------------------------------------------------
        self._positional_index = self.get_positional_index() 
        self._nodeIndex        = self.get_nodeIndex()
        self._galaxyID         = self.get_galaxyID()
        self._topLeafID        = self.get_topLeafID()
        
        #-------------------------------------------------------------------------
        # Getting main progenitor branch, descendants and joining them
        # for this subgroup's full time evolution.
        #-------------------------------------------------------------------------
        self._main_progenitors = self.get_main_progenitors()
        self._main_descendants = self.get_main_descendants()
        self._main_tree        = self.join_main_progenitors_and_descendants()

        #-------------------------------------------------------------------------
        # Dictonary where this subgroup's  property evolution will be 
        #-------------------------------------------------------------------------
        self.evolution = {}

        # Load by default the time information of this merger tree
        self.evolution['aExp'    ]  = self._database.aExp     [self['SnapNum']]
        self.evolution['Redshift']  = self._database.redshifts[self['SnapNum']]
        self.evolution['tUniverse'] = self._database.tUniverse[self['SnapNum']]

    #=============================================================================
    # Methods to get a hold of this object's info
    # during initialisation
    #=============================================================================

    def get_positional_index(self):
        '''
        Returns the array index where the object of interest is stored.
        '''
        return where(self._database['Subhalo/SnapNum'] == self._snap_number)[0][self._subgroup_number]

    def get_nodeIndex(self):
        '''
        Returns the nodeIndex of the tracked subgroup, given by:
        snap_number * 1e12 + file_number * 1e8 + subgroup_number_in_file
        '''
        return self._database['MergerTree/nodeIndex'][self._positional_index]

    def get_galaxyID(self):
        '''
        Returns the unique identifier as given in the depth-first database.
        '''
        return self._database['MergerTree/GalaxyID'][self._positional_index]
    
    def get_topLeafID(self):
        '''
        Returns the galaxyID of this group's earliest redshift main progenitor.
        '''
        return self._database['MergerTree/TopLeafID'][self._positional_index]

    def get_galaxyID_info(self, galaxyID_array):
        '''
        Retrieves positional index and nodeIndex of the specified list of galaxyIDs.

        Parameters
        ----------
        galaxyID_array : ArrayType
            galaxyID values that we want to search for

        Returns
        ----------
        galaxyID_info : dict
            Dictionary holding where to locate galaxyID in this database file (positional_index)
            and the corresponding nodeIndex of these objects (nodeIndex).
        '''

        galaxyID_info = {}
        galaxyID_info['galaxyID']         = galaxyID_array
        galaxyID_info['positional_index'] = quick_search(self._database['MergerTree/GalaxyID'],
                                                         galaxyID_array, self._database._galaxyID_sorter)
        galaxyID_info['nodeIndex']        = self._database['MergerTree/nodeIndex'][galaxyID_info['positional_index']] 
        
        return galaxyID_info

    #=============================================================================
    # Methods related to merger tree descendants/progenitor identification
    #=============================================================================
    def get_main_progenitors(self):
        '''
        Returns the main progenitors of the subgroup
        '''

        all_progenitor_galaxyIDs = arange(self._galaxyID,self._topLeafID+1)
        return self.get_galaxyID_info(all_progenitor_galaxyIDs) 
    
    def get_next_descendant(self, galaxyID):
        '''
        Retrieves galaxyID of the descendant of the specified SUBFIND group.

        Parameters
        -----------
        galaxyID : int
            galaxyID of the subgroup we want to find the descendant of
        '''
        # Find entry corresponding to current galaxyID
        positional_index = quick_search(self._database['MergerTree/GalaxyID'], galaxyID,
                                        self._database._galaxyID_sorter)

        descendant_galaxyID = self._database['MergerTree/DescendantID'][positional_index]

        return descendant_galaxyID

    def get_main_descendants(self):
        '''
        Gets the galaxyID,positional index and nodeIndex of this subgroup's
        descendants.
        '''

        # Iteratively find all descendant galaxyIDs 
        all_descendant_galaxyIDs = []
        next_galaxyID = self.get_next_descendant(self._galaxyID) 
        while next_galaxyID != -1:
            all_descendant_galaxyIDs.append(next_galaxyID[0])
            next_galaxyID    = self.get_next_descendant(next_galaxyID) 
        if not all_descendant_galaxyIDs:
            return None
        
        # Collect results into a dict and return
        main_descendant_dict = self.get_galaxyID_info(asarray(all_descendant_galaxyIDs)[::-1])
        
        return main_descendant_dict
    
    def join_main_progenitors_and_descendants(self):
        '''
        Joins information about progenitors and descendants to access
        the full time evolution of the group.
        '''
        # Method used to reconstruct evolution (past and future) of given object
        if self._main_progenitors is None:
            main_evolutionary_tree = self._main_descendants
        elif self._main_descendants is None:
            main_evolutionary_tree = self._main_progenitors
        else:
            
            main_evolutionary_tree = {}
            for key in self._main_progenitors.keys():
                main_evolutionary_tree[key] = hstack([self._main_descendants[key], self._main_progenitors[key]])
        return main_evolutionary_tree
    
    def get_property_evolution(self, property):
        '''
        Retrieves main progenitor branch evolution of specified property.
        
        Parameters
        -----------
        property: str
            Name of the property to retrieve
        '''
        if property not in self.evolution:
            self.evolution[property] = self._database['Subhalo/%s'%property][()][self._main_progenitors['positional_index']]

        return self.evolution[property]

    def __getitem__(self, property):
        self.get_property_evolution(property)
        return self.evolution[property]

    #=============================================================================
    # Helper methods
    #=============================================================================
    def plot_evolution(self, x_axis, y_axis, x_scale = 'linear', y_scale = 'linear'):
        '''
        Helper function to plot the time evolution of a specified quantity.

        Parameters
        -----------
        x_axis : str
            Name of the time variable to plot as the x coordinate. Should be either
            Redshift, aExp or tUniverse
        y_axis : str
            Name of the variable to choose as the y coordinate.
        x_scale : str, opt
            Scale of x_axis, either linear (default) or log.
        y_scale : str, opt
            Scale of y_axis, either linear (default) or log.
        
        Returns
        -----------
        int
            0 on sucessfull execution
        '''

        fig, ax1 = plt.subplots(1)
        ax1.plot(self[x_axis],self[y_axis])
        ax1.set_xscale(x_scale)
        ax1.set_yscale(y_scale)
        ax1.set_xlabel(x_axis)
        ax1.set_ylabel(y_axis)
        plt.show()

        return 0


    #=============================================================================
    # Property definitions
    #=============================================================================
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