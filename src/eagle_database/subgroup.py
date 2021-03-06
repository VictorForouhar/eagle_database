import matplotlib.pyplot as plt
from .helper_functions import quick_search
from numpy import where, arange, asarray, hstack, zeros, diff

# TODO: useful to get number of progenitors
class Subgroup:

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
        self._lastProgenitorID = self.get_lastProgenitorID()
        
        #-------------------------------------------------------------------------
        # Getting main progenitor branch, descendants and joining them
        # for this subgroup's full time evolution.
        #-------------------------------------------------------------------------
        self._main_progenitors = self.get_main_progenitors()
        self._descendants      = self.get_descendants()
        self._main_merger_tree = self.build_main_merger_tree()

        #-------------------------------------------------------------------------
        # Dictonary where this subgroup's  property evolution will be 
        #-------------------------------------------------------------------------
        self.evolution = {}

        # Load by default the time information of this merger tree
        self.evolution['aExp'    ]  = self._database.aExp     [self['SnapNum']]
        self.evolution['Redshift']  = self._database.redshifts[self['SnapNum']]
        self.evolution['tUniverse'] = self._database.tUniverse[self['SnapNum']]

        self.main_progenitor_branch_length = self.evolution['aExp'].shape[0]
        
        # Identify if and when group is lost from the catalogues
        self._last_resolved_snapshot = self.identify_last_resolved_snapshot()

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

    def get_lastProgenitorID(self):
        '''
        Returns the maximum galaxyID of the progenitors of this group, regardless of 
        progenitor branch.
        '''
        return self._database['MergerTree/LastProgID'][self._positional_index]
    
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

    def get_descendants(self):
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
        descendant_dict = self.get_galaxyID_info(asarray(all_descendant_galaxyIDs)[::-1])
        
        return descendant_dict
    
    def build_main_merger_tree(self):
        '''
        Joins information about progenitors and descendants to access
        the full time evolution of the group.
        '''
        # Method used to reconstruct evolution (past and future) of given object
        if self._main_progenitors is None:
            main_evolutionary_tree = self._descendants
        elif self._descendants is None:
            main_evolutionary_tree = self._main_progenitors
        else:
            
            main_evolutionary_tree = {}
            for key in self._main_progenitors.keys():
                main_evolutionary_tree[key] = hstack([self._descendants[key], self._main_progenitors[key]])
        return main_evolutionary_tree

    def identify_last_resolved_snapshot(self):
        '''
        It identifies when the main branch of this subgroup ends, e.g
        when it has merged with a more massive structure or is no 
        longer resolved.
        '''

        # Make use of the fact that main branch galaxyID values are separated 
        # by 1.
        cumulative_galaxyID_diff = diff(self.main_merger_tree['galaxyID'])


        # Find where and if the group is lost from merger trees
        lost_positional_index = where(cumulative_galaxyID_diff != 1)[0]

        # Group has not been lost case
        if len(lost_positional_index) == 0:
            return -1
        else: 
            last_resolved_galaxyID = self.main_merger_tree['galaxyID'][lost_positional_index[0]+1]
            return self['SnapNum'][lost_positional_index[0]+1]

    #=============================================================================
    # Methods to retrieve evolution of properties
    #=============================================================================
    # TODO: add way to retrieve units of quantities
    def get_property_evolution(self, property):
        '''
        Retrieves main progenitor branch evolution of specified property.
        
        Parameters
        -----------
        property: str
            Name of the property to retrieve
        '''
        if property not in self.evolution:

            # Handling 3D quantities that have been split into different dimensions 
            if (property == 'CentreOfPotential') or (property == 'Velocity'):
                self.evolution[property] = zeros((len(self.evolution['aExp']),3))
                for i, coord in enumerate(['x','y','z']):
                    self.evolution[property][:,i] = self.get_property_evolution('%s_%s'%(property,coord))
            else:
                self.evolution[property] = self._database['Subhalo/%s'%property][()][self._main_merger_tree['positional_index']]

        return self.evolution[property]

    def __getitem__(self, property):
        self.get_property_evolution(property)
        return self.evolution[property]

    #=============================================================================
    # Helper methods (plotting and searching)
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
        # Plot quantity
        ax1.plot(self[x_axis],self[y_axis])
        # Set scale
        ax1.set_xscale(x_scale)
        ax1.set_yscale(y_scale)
        # Set labels
        ax1.set_xlabel(x_axis)
        ax1.set_ylabel(y_axis)
        plt.show()

        return 0

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
    # Property definitions
    #=============================================================================

    @property
    def subgroup_number(self):
        return self._subgroup_number

    @property
    def snap_number(self):
        return self._snap_number
    
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
    def lastProgenitorID(self):
        return self._lastProgenitorID

    @property
    def main_progenitors(self):
        return self._main_progenitors

    @property
    def descendants(self):
        return self._main_progenitors

    @property
    def main_merger_tree(self):
        return self._main_merger_tree
    
    @property
    def last_resolved_snapshot(self):
        return self._last_resolved_snapshot